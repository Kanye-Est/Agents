#!/usr/bin/env python3
"""Passive, fail-closed classic-pcap HTTP decoder for the UTCS local rig.

Input is a full-snaplen tcpdump capture on lo, TCP port 8000, and its stderr.
No sockets, subprocesses, model calls, or packet injection are performed.
Raw HTTP transfer bytes and decoded entity bytes are retained as base64.
Capture completeness is limited to the supplied capture window; the caller
must separately prove the capture started before and ended after the session.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import ipaddress
import json
from pathlib import Path
import re
import struct
import sys

SCHEMA = "utcs_http_capture_v1"
VERSION = "1.0.0"
SERVER_PORT = 8000


def sha(data):
    return hashlib.sha256(data).hexdigest()


def b64(data):
    return base64.b64encode(data).decode("ascii")


class DecodeFailure(Exception):
    def __init__(self, code, detail):
        super().__init__(detail)
        self.code = code
        self.detail = detail


class Decoder:
    def __init__(self):
        self.errors = []
        self.connections = []
        self.active = {}
        self.metadata = {
            "decoder_version": VERSION,
            "packet_count": 0,
            "tcp_packet_count": 0,
            "ignored_non_8000_tcp_packets": 0,
            "model_call_count": 0,
            "http_exchange_count": 0,
            "scope": "classic pcap; loopback IPv4 TCP port 8000; HTTP/1.0 or HTTP/1.1",
            "capture_window_attestation_required": True,
        }

    def error(self, code, detail, **context):
        self.errors.append({"code": code, "detail": detail, **context})

    def tcpdump_stats(self, text):
        names = {
            "tcpdump_packets_captured": r"(?m)^\s*(\d+)\s+packets?\s+captured\s*$",
            "tcpdump_packets_received_by_filter": r"(?m)^\s*(\d+)\s+packets?\s+received by filter\s*$",
            "dropped_by_kernel": r"(?m)^\s*(\d+)\s+packets?\s+dropped by kernel\s*$",
        }
        for name, pattern in names.items():
            values = re.findall(pattern, text)
            if len(values) != 1:
                self.metadata[name] = None
                self.error("tcpdump_statistics_missing_or_ambiguous",
                           f"Expected one {name} count, found {len(values)}")
            else:
                self.metadata[name] = int(values[0])
        interface = re.findall(r"(?m)^\s*(\d+)\s+packets?\s+dropped by interface\s*$", text)
        self.metadata["dropped_by_interface"] = int(interface[0]) if len(interface) == 1 else None
        if len(interface) > 1:
            self.error("tcpdump_statistics_ambiguous", "Multiple interface-drop counts")
        for name in ("dropped_by_kernel", "dropped_by_interface"):
            if self.metadata.get(name):
                self.error("pcap_drops", f"{name}={self.metadata[name]}")
        if re.search(r"(?im)^tcpdump:.*(?:permission denied|cannot |failed|error|no such|invalid |truncated)", text):
            self.error("tcpdump_error_reported", "tcpdump stderr contains an error; inspect original stderr")

    def read_pcap(self, data):
        magic = {
            b"\xd4\xc3\xb2\xa1": ("<", 1000),
            b"\xa1\xb2\xc3\xd4": (">", 1000),
            b"\x4d\x3c\xb2\xa1": ("<", 1),
            b"\xa1\xb2\x3c\x4d": (">", 1),
        }
        if len(data) < 24:
            self.error("pcap_header_truncated", f"Only {len(data)} bytes")
            return
        if data[:4] not in magic:
            self.error("pcap_format_unsupported", f"Magic {data[:4].hex()}; classic pcap required")
            return
        endian, ns_factor = magic[data[:4]]
        major, minor, zone, sigfigs, snaplen, network = struct.unpack(endian + "HHiIII", data[4:24])
        linktype = network & 0xFFFF
        self.metadata.update({
            "pcap_endianness": "little" if endian == "<" else "big",
            "pcap_timestamp_resolution": "nanoseconds" if ns_factor == 1 else "microseconds",
            "pcap_version": [major, minor], "snaplen": snaplen, "linktype": linktype,
            "pcap_network_field": network,
        })
        if (major, minor) != (2, 4):
            self.error("pcap_version_unsupported", f"{major}.{minor}")
        if network != linktype:
            self.error("pcap_linktype_extensions_unsupported", f"network field={network}")
        if linktype not in (0, 1, 101, 108, 113, 276):
            self.error("linktype_unsupported", f"DLT {linktype}")
            return
        if snaplen == 0:
            self.error("pcap_invalid_snaplen", "snaplen is zero")
        pos = 24
        first_ns = last_ns = None
        while pos < len(data):
            index = self.metadata["packet_count"]
            if len(data) - pos < 16:
                self.error("pcap_record_header_truncated", f"At file offset {pos}", packet_index=index)
                break
            sec, fraction, included, original = struct.unpack(endian + "IIII", data[pos:pos + 16])
            pos += 16
            if fraction >= (1000000000 if ns_factor == 1 else 1000000):
                self.error("pcap_invalid_timestamp", f"fraction={fraction}", packet_index=index)
            if included > original:
                self.error("pcap_invalid_packet_lengths", f"included={included}, original={original}", packet_index=index)
            if included > snaplen:
                self.error("pcap_snaplen_inconsistent", f"included={included}, snaplen={snaplen}", packet_index=index)
            if included < original:
                self.error("pcap_packet_truncated", f"included={included}, original={original}", packet_index=index)
            if len(data) - pos < included:
                self.error("pcap_record_data_truncated", f"Need {included}, have {len(data)-pos}", packet_index=index)
                break
            packet = data[pos:pos + included]
            pos += included
            timestamp_ns = sec * 1000000000 + fraction * ns_factor
            if first_ns is None:
                first_ns = timestamp_ns
            last_ns = timestamp_ns
            self.metadata["packet_count"] += 1
            try:
                self.packet(packet, linktype, endian, index, timestamp_ns)
            except DecodeFailure as e:
                self.error(e.code, e.detail, packet_index=index)
            except (ValueError, struct.error, IndexError) as e:
                self.error("packet_decoder_error", str(e), packet_index=index)
        self.metadata["first_packet_time_ns"] = first_ns
        self.metadata["last_packet_time_ns"] = last_ns
        expected = self.metadata.get("tcpdump_packets_captured")
        if expected is not None and expected != self.metadata["packet_count"]:
            self.error("pcap_packet_count_mismatch",
                       f"pcap records={self.metadata['packet_count']}, tcpdump captured={expected}")

    def packet(self, packet, linktype, endian, index, timestamp_ns):
        if linktype == 1:
            if len(packet) < 14:
                raise DecodeFailure("ethernet_truncated", "Ethernet header shorter than 14")
            protocol = struct.unpack("!H", packet[12:14])[0]
            pos = 14
            vlan_count = 0
            while protocol in (0x8100, 0x88A8, 0x9100):
                if len(packet) < pos + 4:
                    raise DecodeFailure("vlan_truncated", "Incomplete VLAN tag")
                protocol = struct.unpack("!H", packet[pos + 2:pos + 4])[0]
                pos += 4
                vlan_count += 1
                if vlan_count > 4:
                    raise DecodeFailure("vlan_stack_unsupported", "More than four VLAN tags")
        elif linktype == 113:
            if len(packet) < 16:
                raise DecodeFailure("sll_truncated", "SLL header shorter than 16")
            protocol, pos = struct.unpack("!H", packet[14:16])[0], 16
        elif linktype == 276:
            if len(packet) < 20:
                raise DecodeFailure("sll2_truncated", "SLL2 header shorter than 20")
            protocol, pos = struct.unpack("!H", packet[:2])[0], 20
        elif linktype in (0, 108):
            if len(packet) < 4:
                raise DecodeFailure("loopback_header_truncated", "DLT_NULL/LOOP header shorter than 4")
            family = struct.unpack(("!" if linktype == 108 else endian) + "I", packet[:4])[0]
            protocol, pos = (0x0800 if family == 2 else 0x86DD if family in (10, 24, 28, 30) else family), 4
        else:
            if not packet:
                raise DecodeFailure("raw_packet_empty", "Empty DLT_RAW packet")
            protocol, pos = (0x0800 if packet[0] >> 4 == 4 else 0x86DD), 0
        if protocol != 0x0800:
            raise DecodeFailure("network_protocol_unsupported",
                                f"Ethertype/family {protocol:#x}; unknown filtered packet cannot be ignored")
        ip = packet[pos:]
        if len(ip) < 20 or ip[0] >> 4 != 4:
            raise DecodeFailure("ipv4_header_invalid", "Missing or invalid IPv4 header")
        ihl = (ip[0] & 15) * 4
        total = struct.unpack("!H", ip[2:4])[0]
        if ihl < 20 or ihl > len(ip) or total < ihl:
            raise DecodeFailure("ipv4_lengths_invalid", f"ihl={ihl}, total={total}, captured={len(ip)}")
        if total > len(ip):
            raise DecodeFailure("ipv4_packet_truncated", f"IPv4 total={total}, captured={len(ip)}")
        if struct.unpack("!H", ip[6:8])[0] & 0x3FFF:
            raise DecodeFailure("ipv4_fragment_unsupported", "Fragmented IPv4 datagram")
        if ip[9] != 6:
            raise DecodeFailure("transport_unsupported", f"IPv4 protocol={ip[9]}; filtered packet is not TCP")
        src, dst = str(ipaddress.IPv4Address(ip[12:16])), str(ipaddress.IPv4Address(ip[16:20]))
        tcp = ip[ihl:total]
        if len(tcp) < 20:
            raise DecodeFailure("tcp_header_truncated", "TCP header shorter than 20")
        sport, dport, seq, ack = struct.unpack("!HHII", tcp[:12])
        hlen = (tcp[12] >> 4) * 4
        if hlen < 20 or hlen > len(tcp):
            raise DecodeFailure("tcp_header_invalid", f"hlen={hlen}, captured TCP={len(tcp)}")
        if SERVER_PORT not in (sport, dport):
            self.metadata["ignored_non_8000_tcp_packets"] += 1
            return
        if sport == SERVER_PORT and dport == SERVER_PORT:
            raise DecodeFailure("tcp_direction_ambiguous", "Both endpoint ports are 8000")
        if not ipaddress.IPv4Address(src).is_loopback or not ipaddress.IPv4Address(dst).is_loopback:
            self.error("nonloopback_endpoint", f"{src}:{sport} -> {dst}:{dport}", packet_index=index)
        self.metadata["tcp_packet_count"] += 1
        direction = "server" if sport == SERVER_PORT else "client"
        client = (dst, dport) if direction == "server" else (src, sport)
        server = (src, sport) if direction == "server" else (dst, dport)
        key = (client, server)
        flags = tcp[13]
        syn, ack_flag, fin, rst = bool(flags & 2), bool(flags & 16), bool(flags & 1), bool(flags & 4)
        conn = self.active.get(key)
        if conn is None or (direction == "client" and syn and not ack_flag
                            and conn["streams"]["client"]["syn"] not in (None, seq)):
            generation = 0 if conn is None else conn["generation"] + 1
            if conn is not None and not conn["closed"]:
                self.error("tcp_tuple_reused_without_observed_close", str(key), packet_index=index)
            conn = {
                "connection_id": f"c{len(self.connections):04d}",
                "client": list(client), "server": list(server), "generation": generation,
                "first_packet_index": index, "first_time_ns": timestamp_ns,
                "closed": False, "streams": {"client": self.new_stream(), "server": self.new_stream()},
            }
            self.connections.append(conn)
            self.active[key] = conn
        stream = conn["streams"][direction]
        peer = conn["streams"]["server" if direction == "client" else "client"]
        if syn:
            if stream["syn"] is not None and stream["syn"] != seq:
                self.error("tcp_conflicting_syn", f"{direction} SYN sequence changed",
                           connection_id=conn["connection_id"], packet_index=index)
            stream["syn"] = seq
        if ack_flag:
            peer["acks"].append((ack, index))
        payload = tcp[hlen:]
        if payload:
            stream["segments"].append({
                "seq": (seq + int(syn)) & 0xFFFFFFFF, "data": payload,
                "packet_index": index, "time_ns": timestamp_ns,
            })
        if fin:
            stream["fins"].append(((seq + int(syn) + len(payload)) & 0xFFFFFFFF, index))
        if rst:
            stream["rst"] = True
            self.error("tcp_reset", f"{direction} RST observed", connection_id=conn["connection_id"], packet_index=index)
        conn["closed"] = rst or all(s["fins"] for s in conn["streams"].values())

    @staticmethod
    def new_stream():
        return {"syn": None, "segments": [], "acks": [], "fins": [], "rst": False}

    @staticmethod
    def relative(seq, base):
        value = (seq - base) & 0xFFFFFFFF
        return value if value < 0x80000000 else value - 0x100000000

    def reassemble(self, conn, direction):
        s = conn["streams"][direction]
        context = {"connection_id": conn["connection_id"], "direction": direction}
        segments = s["segments"]
        if s["syn"] is None:
            if segments or conn["streams"]["server" if direction == "client" else "client"]["segments"]:
                self.error("tcp_syn_missing", "Capture did not observe direction's SYN", **context)
            reference = segments[0]["seq"] if segments else 0
            minimum = min((self.relative(seg["seq"], reference) for seg in segments), default=0)
            base = (reference + minimum) & 0xFFFFFFFF
        else:
            base = (s["syn"] + 1) & 0xFFFFFFFF
        ordered = sorted(({**seg, "offset": self.relative(seg["seq"], base)} for seg in segments),
                         key=lambda seg: (seg["offset"], seg["packet_index"]))
        buf = bytearray()
        retransmissions = 0
        gap = False
        for seg in ordered:
            start, payload = seg["offset"], seg["data"]
            if start < 0:
                self.error("tcp_data_before_origin", f"offset={start}", packet_index=seg["packet_index"], **context)
                continue
            if start > len(buf):
                self.error("tcp_gap", f"Missing stream bytes [{len(buf)},{start})",
                           packet_index=seg["packet_index"], **context)
                gap = True
                break
            overlap = min(len(payload), len(buf) - start)
            if overlap:
                retransmissions += 1
                if bytes(buf[start:start + overlap]) != payload[:overlap]:
                    self.error("tcp_overlap_conflict", f"Inconsistent overlapping bytes at offset {start}",
                               packet_index=seg["packet_index"], **context)
            if len(payload) > overlap:
                buf.extend(payload[overlap:])
        fin_offsets = [self.relative(value, base) for value, _ in s["fins"]]
        for offset in fin_offsets:
            if offset != len(buf):
                self.error("tcp_fin_data_mismatch", f"FIN offset={offset}, reconstructed bytes={len(buf)}", **context)
        ack_offsets = [self.relative(value, base) for value, _ in s["acks"]]
        max_ack = max((value for value in ack_offsets if value >= 0), default=None)
        allowed = len(buf) + int(bool(fin_offsets) and all(x == len(buf) for x in fin_offsets))
        if max_ack is not None and max_ack > allowed:
            self.error("tcp_acknowledges_uncaptured_data",
                       f"Peer ACK offset={max_ack}, captured sequence extent={allowed}", **context)
        result = {
            "data": bytes(buf), "ordered_segments": ordered,
            "fin_complete": bool(fin_offsets) and all(x == len(buf) for x in fin_offsets) and not gap,
            "summary": {
                "origin_sequence": base, "syn_observed": s["syn"] is not None,
                "payload_segment_count": len(segments), "retransmission_segments": retransmissions,
                "contiguous_bytes": len(buf), "contiguous_sha256": sha(bytes(buf)),
                "fin_offsets": fin_offsets, "max_peer_ack_offset": max_ack, "rst_observed": s["rst"],
            },
        }
        return result

    def json_value(self, text, **context):
        duplicates = []
        def pairs(items):
            result = {}
            for key, value in items:
                if key in result:
                    duplicates.append(key)
                result[key] = value
            return result
        def constant(value):
            raise ValueError(f"Non-JSON constant {value}")
        try:
            value = json.loads(text, object_pairs_hook=pairs, parse_constant=constant)
        except (ValueError, TypeError) as e:
            self.error("json_invalid", str(e), **context)
            return None
        if duplicates:
            self.error("json_duplicate_keys", repr(duplicates), **context)
        return value

    @staticmethod
    def headers(lines):
        fields, values = [], {}
        token = re.compile(rb"[!#$%&'*+\-.^_\x60|~0-9A-Za-z]+")
        for line in lines:
            if not line or line[:1] in (b" ", b"\t") or b":" not in line:
                raise DecodeFailure("http_header_invalid", repr(line[:160]))
            name, value = line.split(b":", 1)
            if token.fullmatch(name) is None:
                raise DecodeFailure("http_header_name_invalid", repr(name))
            if any(c < 32 and c != 9 for c in value) or 127 in value:
                raise DecodeFailure("http_header_control_character", repr(name))
            name = name.decode("ascii")
            value = value.decode("latin1").strip(" \t")
            fields.append([name, value])
            values.setdefault(name.lower(), []).append(value)
        return fields, values

    @staticmethod
    def chunked(data, pos):
        chunks = []
        while True:
            end = data.find(b"\r\n", pos)
            if end < 0:
                raise DecodeFailure("http_chunk_size_truncated", f"Offset {pos}")
            line = data[pos:end]
            size_text = line.split(b";", 1)[0]
            if not size_text or re.fullmatch(rb"[0-9a-fA-F]+", size_text) is None:
                raise DecodeFailure("http_chunk_size_invalid", repr(line[:160]))
            size = int(size_text, 16)
            pos = end + 2
            if size == 0:
                if data[pos:pos + 2] == b"\r\n":
                    return b"".join(chunks), pos + 2, []
                trailer_end = data.find(b"\r\n\r\n", pos)
                if trailer_end < 0:
                    raise DecodeFailure("http_chunk_trailers_truncated", f"Offset {pos}")
                trailers, _ = Decoder.headers(data[pos:trailer_end].split(b"\r\n"))
                return b"".join(chunks), trailer_end + 4, trailers
            if size > len(data) - pos or len(data) - pos - size < 2:
                raise DecodeFailure("http_chunk_data_truncated", f"Need chunk size {size} at {pos}")
            chunks.append(data[pos:pos + size])
            pos += size
            if data[pos:pos + 2] != b"\r\n":
                raise DecodeFailure("http_chunk_terminator_invalid", f"Offset {pos}")
            pos += 2

    def http_message(self, stream, pos, kind, request_method=None):
        data = stream["data"]
        begin = pos
        header_end = data.find(b"\r\n\r\n", pos)
        if header_end < 0:
            raise DecodeFailure("http_headers_truncated", f"Offset {pos}")
        lines = data[pos:header_end].split(b"\r\n")
        first = lines[0]
        if kind == "request":
            match = re.fullmatch(rb"([!#$%&'*+\-.^_\x60|~0-9A-Z]+) ([^\x00-\x20\x7f]+) (HTTP/1\.[01])", first)
            if not match:
                raise DecodeFailure("http_request_line_invalid", repr(first[:200]))
            method, path, version = (value.decode("ascii") for value in match.groups())
            item = {"method": method, "path": path, "version": version}
            status = None
        else:
            match = re.fullmatch(rb"(HTTP/1\.[01]) ([0-9]{3})(?: ([^\r\n]*))?", first)
            if not match:
                raise DecodeFailure("http_status_line_invalid", repr(first[:200]))
            version, code, reason = match.groups()
            status = int(code)
            item = {"status": status, "version": version.decode("ascii"),
                    "reason": (reason or b"").decode("latin1")}
            if not 100 <= status <= 599:
                raise DecodeFailure("http_status_invalid", f"Status {status}")
            if status == 101:
                raise DecodeFailure("http_upgrade_unsupported", "HTTP 101 switching protocols")
        fields, values = self.headers(lines[1:])
        headers = {name: ", ".join(value) for name, value in values.items()}
        pos = header_end + 4
        transfer = [value.strip().lower() for field in values.get("transfer-encoding", []) for value in field.split(",")]
        lengths = [value.strip() for field in values.get("content-length", []) for value in field.split(",")]
        if transfer and lengths:
            raise DecodeFailure("http_ambiguous_framing", "Both Transfer-Encoding and Content-Length")
        if lengths and (any(re.fullmatch(r"[0-9]+", value) is None for value in lengths)
                        or len(set(int(value) for value in lengths)) != 1):
            raise DecodeFailure("http_content_length_invalid", repr(lengths))
        no_body = kind == "response" and (request_method == "HEAD" or status in (204, 304) or 100 <= status < 200)
        trailers = []
        if no_body:
            body, framing = b"", "no_body"
        elif transfer:
            if transfer != ["chunked"]:
                raise DecodeFailure("http_transfer_encoding_unsupported", repr(transfer))
            body, pos, trailers = self.chunked(data, pos)
            framing = "chunked"
        elif lengths:
            length = int(lengths[0])
            if length > len(data) - pos:
                raise DecodeFailure("http_content_length_truncated", f"Need {length} body bytes, have {len(data)-pos}")
            body = data[pos:pos + length]
            pos += length
            framing = "content_length"
        elif kind == "request":
            body, framing = b"", "no_body"
        else:
            if not stream["fin_complete"]:
                raise DecodeFailure("http_close_delimited_without_fin", "No length/chunking and no complete FIN")
            body, pos, framing = data[pos:], len(data), "connection_close"
        raw = data[begin:pos]
        owners = [seg for seg in stream["ordered_segments"]
                  if seg["offset"] <= begin < seg["offset"] + len(seg["data"])]
        owner = min(owners, key=lambda seg: seg["packet_index"]) if owners else None
        item.update({
            "headers": headers, "header_fields": fields, "trailers": trailers, "framing": framing,
            "body_base64": b64(body), "body_sha256": sha(body), "raw_base64": b64(raw),
            "raw_sha256": sha(raw), "stream_start_offset": begin, "stream_end_offset": pos,
            "start_packet_index": owner["packet_index"] if owner else None,
            "start_time_ns": owner["time_ns"] if owner else None,
            "body_text": None, "json": None,
        })
        try:
            item["body_text"] = body.decode("utf-8")
        except UnicodeDecodeError as e:
            self.error("http_body_not_utf8", str(e), http_kind=kind, stream_offset=begin)
        encoding = headers.get("content-encoding", "").lower()
        if encoding not in ("", "identity"):
            self.error("http_content_encoding_unsupported", encoding, http_kind=kind, stream_offset=begin)
        content_type = headers.get("content-type", "").split(";", 1)[0].strip().lower()
        if body and item["body_text"] is not None and (content_type == "application/json" or content_type.endswith("+json")):
            item["json"] = self.json_value(item["body_text"], http_kind=kind, stream_offset=begin)
        return item, pos

    def sse(self, body, context):
        events = []
        lines = re.split(r"\r\n|\r|\n", body)
        if lines and lines[0].startswith("\ufeff"):
            lines[0] = lines[0][1:]
        pending_data, field_lines = [], []
        event_type, event_id = "message", None
        done = False
        def dispatch(terminated):
            nonlocal pending_data, field_lines, event_type, event_id, done
            if pending_data:
                data = "\n".join(pending_data)
                is_done = data == "[DONE]"
                if done:
                    self.error("sse_data_after_done", "Another event followed [DONE]", **context)
                item = {
                    "index": len(events), "event": event_type, "id": event_id,
                    "data": data, "json": None, "is_done": is_done,
                    "terminated": terminated, "field_lines": field_lines,
                }
                if not is_done:
                    item["json"] = self.json_value(data, sse_index=item["index"], **context)
                    if not isinstance(item["json"], dict):
                        self.error("sse_nonobject_data", "Expected JSON object in OpenAI SSE", sse_index=item["index"], **context)
                    elif "error" in item["json"]:
                        self.error("sse_error_payload", repr(item["json"]["error"]), sse_index=item["index"], **context)
                if event_type == "error":
                    self.error("sse_error_event", "SSE event type is error", **context)
                events.append(item)
                done = done or (is_done and terminated)
            pending_data, field_lines, event_type = [], [], "message"
        for i, line in enumerate(lines):
            # split creates a final sentinel after a line ending; it is not a second line ending.
            if i == len(lines) - 1 and line == "":
                break
            if line == "":
                dispatch(True)
                continue
            if line.startswith(":"):
                continue
            name, separator, value = line.partition(":")
            if separator and value.startswith(" "):
                value = value[1:]
            field_lines.append(line)
            if name == "data":
                pending_data.append(value)
            elif name == "event":
                event_type = value
            elif name == "id":
                if "\x00" in value:
                    self.error("sse_id_invalid", "NUL in SSE id", **context)
                event_id = value
            elif name == "retry":
                if re.fullmatch(r"[0-9]+", value) is None:
                    self.error("sse_retry_invalid", value, **context)
            else:
                self.error("sse_unknown_field", name, **context)
        if pending_data or field_lines:
            self.error("sse_unterminated_event", "SSE event lacks terminating blank line", **context)
            dispatch(False)
        if not done:
            self.error("sse_missing_done", "No complete [DONE] marker", **context)
        return events, done

    def exchanges(self):
        output, summaries, unparsed = [], [], []
        for conn in self.connections:
            client, server = self.reassemble(conn, "client"), self.reassemble(conn, "server")
            requests, pos = [], 0
            while pos < len(client["data"]):
                try:
                    request, pos = self.http_message(client, pos, "request")
                    is_model = request["method"] == "POST" and request["path"] == "/v1/chat/completions"
                    if is_model:
                        if request["json"] is None and request["body_text"] is not None:
                            request["json"] = self.json_value(request["body_text"], connection_id=conn["connection_id"], http_kind="request")
                        if not isinstance(request["json"], dict):
                            self.error("model_request_not_json_object", "Model POST body is not a JSON object", connection_id=conn["connection_id"])
                    requests.append((request, is_model))
                except (DecodeFailure, UnicodeDecodeError) as e:
                    self.error(getattr(e, "code", "http_ascii_invalid"), str(e),
                               connection_id=conn["connection_id"], direction="client", stream_offset=pos)
                    unparsed.append({"connection_id": conn["connection_id"], "direction": "client",
                                     "stream_offset": pos, "base64": b64(client["data"][pos:])})
                    break
            pos = 0
            for index, (request, is_model) in enumerate(requests):
                response, interim = None, []
                try:
                    while pos < len(server["data"]):
                        candidate, pos = self.http_message(server, pos, "response", request["method"])
                        if 100 <= candidate["status"] < 200:
                            interim.append(candidate)
                            continue
                        response = candidate
                        break
                    if response is None:
                        self.error("http_response_missing", "Request has no final response",
                                   connection_id=conn["connection_id"], exchange_index=index)
                    else:
                        response.update({"sse_events": [], "done": True})
                        content_type = response["headers"].get("content-type", "").split(";", 1)[0].strip().lower()
                        context = {"connection_id": conn["connection_id"], "exchange_index": index}
                        stream_expected = is_model and isinstance(request["json"], dict) and request["json"].get("stream") is True
                        if content_type == "text/event-stream":
                            response["format"] = "sse"
                            if response["body_text"] is None:
                                response["done"] = False
                            else:
                                response["sse_events"], response["done"] = self.sse(response["body_text"], context)
                        else:
                            response["format"] = "json" if response["json"] is not None else "other"
                            if stream_expected:
                                self.error("model_stream_response_not_sse", content_type, **context)
                                response["done"] = False
                            if is_model and response["json"] is None and response["body_text"] is not None:
                                response["json"] = self.json_value(response["body_text"], http_kind="response", **context)
                            if is_model and not isinstance(response["json"], dict):
                                self.error("model_response_not_json_object", "Non-stream model response lacks JSON object", **context)
                                response["done"] = False
                        if is_model and response["status"] != 200:
                            self.error("model_http_error", f"HTTP {response['status']}", **context)
                            response["done"] = False
                        if is_model and isinstance(response["json"], dict) and "error" in response["json"]:
                            self.error("model_json_error", repr(response["json"]["error"]), **context)
                            response["done"] = False
                except (DecodeFailure, UnicodeDecodeError) as e:
                    self.error(getattr(e, "code", "http_ascii_invalid"), str(e),
                               connection_id=conn["connection_id"], direction="server", stream_offset=pos)
                    unparsed.append({"connection_id": conn["connection_id"], "direction": "server",
                                     "stream_offset": pos, "base64": b64(server["data"][pos:])})
                    pos = len(server["data"])
                output.append({
                    "connection_id": conn["connection_id"], "exchange_index": index,
                    "is_model_call": is_model, "request": request, "response": response,
                    "interim_responses": interim,
                    "request_start_packet_index": request["start_packet_index"],
                    "request_start_time_ns": request["start_time_ns"],
                })
            if pos < len(server["data"]):
                self.error("http_unmatched_response_bytes", f"{len(server['data'])-pos} server bytes unpaired",
                           connection_id=conn["connection_id"], stream_offset=pos)
                unparsed.append({"connection_id": conn["connection_id"], "direction": "server",
                                 "stream_offset": pos, "base64": b64(server["data"][pos:])})
            summaries.append({
                "connection_id": conn["connection_id"], "client": conn["client"], "server": conn["server"],
                "generation": conn["generation"], "first_packet_index": conn["first_packet_index"],
                "client_stream": client["summary"], "server_stream": server["summary"],
                "http_request_count": len(requests),
            })
        output.sort(key=lambda e: (e["request_start_packet_index"] if e["request_start_packet_index"] is not None else -1,
                                   e["connection_id"], e["exchange_index"]))
        if not output:
            self.error("no_http_exchanges", "No decodable HTTP exchange in capture")
        self.metadata["http_exchange_count"] = len(output)
        self.metadata["model_call_count"] = sum(e["is_model_call"] for e in output)
        return output, summaries, unparsed


def decode_capture(pcap_bytes, tcpdump_stderr, pcap_path="<memory>", tcpdump_stderr_path="<memory>"):
    decoder = Decoder()
    stderr_bytes = tcpdump_stderr.encode("utf-8") if isinstance(tcpdump_stderr, str) else tcpdump_stderr
    try:
        stderr_text = stderr_bytes.decode("utf-8")
    except UnicodeDecodeError:
        stderr_text = stderr_bytes.decode("utf-8", errors="replace")
        decoder.error("tcpdump_stderr_not_utf8", "stderr contains undecodable UTF-8")
    decoder.metadata.update({
        "pcap_path": str(pcap_path), "pcap_sha256": sha(pcap_bytes), "pcap_size_bytes": len(pcap_bytes),
        "tcpdump_stderr_path": str(tcpdump_stderr_path), "tcpdump_stderr_sha256": sha(stderr_bytes),
    })
    decoder.tcpdump_stats(stderr_text)
    decoder.read_pcap(pcap_bytes)
    exchanges, connections, unparsed = decoder.exchanges()
    return {"schema": SCHEMA, "complete": not decoder.errors, "errors": decoder.errors,
            "metadata": decoder.metadata, "exchanges": exchanges, "connections": connections,
            "unparsed_streams": unparsed}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pcap", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--tcpdump-stderr", required=True)
    args = parser.parse_args()
    try:
        report = decode_capture(Path(args.pcap).read_bytes(), Path(args.tcpdump_stderr).read_bytes(),
                                str(Path(args.pcap).resolve()), str(Path(args.tcpdump_stderr).resolve()))
    except (OSError, ValueError, struct.error) as error:
        report = {"schema": SCHEMA, "complete": False,
                  "errors": [{"code": "input_or_decoder_error", "detail": str(error)}],
                  "metadata": {"decoder_version": VERSION, "pcap_path": args.pcap,
                               "tcpdump_stderr_path": args.tcpdump_stderr}, "exchanges": [],
                  "connections": [], "unparsed_streams": []}
    encoded = json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True) + "\n"
    with Path(args.output).open("x", encoding="utf-8") as out:
        out.write(encoded)
    print(json.dumps({"schema": SCHEMA, "complete": report["complete"],
                      "error_count": len(report["errors"]), "exchanges": len(report["exchanges"]),
                      "model_call_count": report["metadata"].get("model_call_count"),
                      "output": str(Path(args.output).resolve()),
                      "output_sha256": sha(encoded.encode("utf-8"))}, sort_keys=True))
    return 0 if report["complete"] else 2


if __name__ == "__main__":
    sys.exit(main())
