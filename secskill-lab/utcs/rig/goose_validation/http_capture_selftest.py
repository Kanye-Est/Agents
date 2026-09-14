#!/usr/bin/env python3
"""In-memory synthetic tests. No sockets, files, subprocesses or model calls."""
import base64
import hashlib
import json
import struct
import sys
from http_capture import decode_capture


def packet(direction, seq, ack, flags, payload=b"", client_port=41001):
    return {"direction": direction, "seq": seq & 0xFFFFFFFF, "ack": ack & 0xFFFFFFFF,
            "flags": flags, "payload": payload, "client_port": client_port}


def connection(request, response, *, client_port=41001, cseq=1000, sseq=9000,
               req_sizes=None, resp_sizes=None, close=True):
    cbase, sbase = (cseq + 1) & 0xFFFFFFFF, (sseq + 1) & 0xFFFFFFFF
    out = [packet("c", cseq, 0, 2, client_port=client_port),
           packet("s", sseq, cbase, 18, client_port=client_port),
           packet("c", cbase, sbase, 16, client_port=client_port)]
    def pieces(data, sizes):
        if sizes is None:
            return [data] if data else []
        result, offset = [], 0
        for size in sizes:
            result.append(data[offset:offset+size])
            offset += size
        if offset < len(data):
            result.append(data[offset:])
        return [p for p in result if p]
    offset = 0
    for p in pieces(request, req_sizes):
        out.append(packet("c", cbase + offset, sbase, 24, p, client_port))
        offset += len(p)
    out.append(packet("s", sbase, cbase + len(request), 16, client_port=client_port))
    offset = 0
    for p in pieces(response, resp_sizes):
        out.append(packet("s", sbase + offset, cbase + len(request), 24, p, client_port))
        offset += len(p)
    out.append(packet("c", cbase + len(request), sbase + len(response), 16, client_port=client_port))
    if close:
        out.extend([
            packet("c", cbase + len(request), sbase + len(response), 17, client_port=client_port),
            packet("s", sbase + len(response), cbase + len(request) + 1, 16, client_port=client_port),
            packet("s", sbase + len(response), cbase + len(request) + 1, 17, client_port=client_port),
            packet("c", cbase + len(request) + 1, sbase + len(response) + 1, 16, client_port=client_port),
        ])
    return out


def frame(p, linktype=1):
    sport, dport = (p["client_port"], 8000) if p["direction"] == "c" else (8000, p["client_port"])
    tcp = struct.pack("!HHIIBBHHH", sport, dport, p["seq"], p["ack"], 5 << 4,
                      p["flags"], 65535, 0, 0) + p["payload"]
    ip = struct.pack("!BBHHHBBH4s4s", 0x45, 0, 20+len(tcp), 0, 0x4000, 64, 6, 0,
                     b"\x7f\x00\x00\x01", b"\x7f\x00\x00\x01") + tcp
    if linktype == 1:
        return b"\x00" * 12 + struct.pack("!H", 0x0800) + ip
    if linktype == 113:
        return struct.pack("!HHH8sH", 0, 772, 6, b"\x00"*8, 0x0800) + ip
    if linktype == 276:
        return struct.pack("!HHIHBB8s", 0x0800, 0, 1, 772, 0, 6, b"\x00"*8) + ip
    if linktype == 0:
        return struct.pack("<I", 2) + ip
    if linktype == 108:
        return struct.pack("!I", 2) + ip
    if linktype == 101:
        return ip
    return b"\x00" * 12 + struct.pack("!H", 0x0800) + ip


def pcap(packets, linktype=1, endian="<", nano=False):
    magic = (b"\x4d\x3c\xb2\xa1" if nano else b"\xd4\xc3\xb2\xa1") if endian == "<" else (
        b"\xa1\xb2\x3c\x4d" if nano else b"\xa1\xb2\xc3\xd4")
    out = magic + struct.pack(endian+"HHiIII", 2, 4, 0, 0, 262144, linktype)
    for i, p in enumerate(packets):
        raw = p if isinstance(p, bytes) else frame(p, linktype)
        out += struct.pack(endian+"IIII", 1700000000, i*100, len(raw), len(raw)) + raw
    return out


def stderr(count, drops=0):
    return f"tcpdump: listening on lo, link-type EN10MB, snapshot length 262144 bytes\n{count} packets captured\n{count*2} packets received by filter\n{drops} packets dropped by kernel\n"


def decode(packets, **kwargs):
    linktype = kwargs.pop("linktype", 1)
    endian = kwargs.pop("endian", "<")
    nano = kwargs.pop("nano", False)
    drops = kwargs.pop("drops", 0)
    assert not kwargs
    return decode_capture(pcap(packets, linktype, endian, nano), stderr(len(packets), drops))


def req(stream=True, text="请整理 README。"):
    body = json.dumps({"model": "qwen3-32b-awq-native-fc", "stream": stream,
                       "messages": [{"role": "system", "content": "Normal system."},
                                    {"role": "user", "content": text}],
                       "tools": []}, ensure_ascii=False, separators=(",", ":")).encode()
    return (b"POST /v1/chat/completions HTTP/1.1\r\nHost: 127.0.0.1:8000\r\n"
            b"Content-Type: application/json\r\nContent-Length: " + str(len(body)).encode() + b"\r\n\r\n" + body)


def nonstream(text="clean"):
    body = json.dumps({"id": "chatcmpl-fixture", "choices": [{"index": 0, "message": {
        "role": "assistant", "content": text}, "finish_reason": "stop"}]},
        ensure_ascii=False, separators=(",", ":")).encode()
    return (b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: "
            + str(len(body)).encode() + b"\r\n\r\n" + body)


EVENTS = [
    {"id": "chatcmpl-fixture", "choices": [{"index": 0, "delta": {"role": "assistant", "reasoning_content": "inspect"}}]},
    {"id": "chatcmpl-fixture", "choices": [{"index": 0, "delta": {"content": "好的"}}]},
    {"id": "chatcmpl-fixture", "choices": [{"index": 0, "delta": {"tool_calls": [{
        "index": 0, "id": "call-1", "type": "function", "function": {
            "name": "utcs_mdclean__md_clean", "arguments": "{\"text\":\"#  A\\r\\n\"}"}}]}}]},
    {"id": "chatcmpl-fixture", "choices": [{"index": 0, "delta": {}, "finish_reason": "tool_calls"}]},
    {"id": "chatcmpl-fixture", "choices": [], "usage": {"prompt_tokens": 7, "completion_tokens": 9}},
]
SSE = b"".join(b"data: " + json.dumps(e, ensure_ascii=False, separators=(",", ":")).encode() + b"\n\n" for e in EVENTS) + b"data: [DONE]\n\n"


def chunked_response(body=SSE, trailer=False):
    sizes = (1, 3, 13, 29, 2, 89)
    offset, encoded = 0, b""
    for n in sizes:
        p = body[offset:offset+n]
        offset += len(p)
        if p:
            encoded += f"{len(p):x};test=yes\r\n".encode()+p+b"\r\n"
    if offset < len(body):
        p = body[offset:]
        encoded += f"{len(p):x}\r\n".encode()+p+b"\r\n"
    encoded += b"0\r\nX-Fixture: yes\r\n\r\n" if trailer else b"0\r\n\r\n"
    return (b"HTTP/1.1 200 OK\r\nContent-Type: text/event-stream; charset=utf-8\r\n"
            b"Transfer-Encoding: chunked\r\n\r\n" + encoded)


def assert_ok(report):
    assert report["complete"] is True, report["errors"]
    assert report["errors"] == []


def assert_error(report, code):
    assert report["complete"] is False
    assert any(e["code"] == code for e in report["errors"]), (code, report["errors"])


RESULTS = []


def test(name, fn):
    try:
        fn()
        RESULTS.append({"name": name, "passed": True})
    except Exception as e:
        RESULTS.append({"name": name, "passed": False, "error": repr(e)})


def t_json():
    request, response = req(False), nonstream("clean\n")
    report = decode(connection(request, response))
    assert_ok(report)
    e = report["exchanges"][0]
    assert e["is_model_call"] and report["metadata"]["model_call_count"] == 1
    assert base64.b64decode(e["request"]["raw_base64"]) == request
    assert base64.b64decode(e["response"]["raw_base64"]) == response
    assert e["response"]["json"]["choices"][0]["message"]["content"] == "clean\n"
    assert e["request"]["body_sha256"] == hashlib.sha256(base64.b64decode(e["request"]["body_base64"])).hexdigest()


def t_chunked():
    request, response = req(True), chunked_response(trailer=True)
    report = decode(connection(request, response, req_sizes=[1, 9, 31], resp_sizes=[3, 11, 97, 4, 53]))
    assert_ok(report)
    e = report["exchanges"][0]["response"]
    assert e["body_text"].encode() == SSE
    assert e["done"] and e["trailers"] == [["X-Fixture", "yes"]]
    assert [v["json"] for v in e["sse_events"][:-1]] == EVENTS
    assert e["sse_events"][-1]["is_done"] is True
    assert e["sse_events"][2]["json"]["choices"][0]["delta"]["tool_calls"][0]["function"]["arguments"] == "{\"text\":\"#  A\\r\\n\"}"


def t_keepalive():
    requests = req(False, "first") + req(True, "second")
    responses = nonstream("first") + chunked_response()
    report = decode(connection(requests, responses, req_sizes=[13, 251, 3], resp_sizes=[79, 83, 11]))
    assert_ok(report)
    assert [e["exchange_index"] for e in report["exchanges"]] == [0, 1]
    assert report["metadata"]["model_call_count"] == 2
    assert report["exchanges"][1]["request"]["json"]["messages"][1]["content"] == "second"


def t_retransmit_out_of_order():
    packets = connection(req(True), chunked_response(), req_sizes=[20, 20, 20], resp_sizes=[20, 20])
    # Move the second request piece before the first, then retransmit the first.
    a, b = packets[3], packets[4]
    packets[3], packets[4] = b, a
    packets.insert(5, dict(a))
    report = decode(packets)
    assert_ok(report)
    assert report["connections"][0]["client_stream"]["retransmission_segments"] >= 1


def t_overlap_conflict():
    packets = connection(req(False), nonstream())
    first = packets[3]
    bad = dict(first)
    bad["payload"] = b"X" + first["payload"][1:]
    packets.insert(4, bad)
    assert_error(decode(packets), "tcp_overlap_conflict")


def t_gap():
    packets = connection(req(True), chunked_response(), req_sizes=[20, 20, 20])
    del packets[4]
    assert_error(decode(packets), "tcp_gap")


def t_missing_tail_ack():
    packets = connection(req(False), nonstream(), close=False)
    packets[3] = {**packets[3], "payload": packets[3]["payload"][:-7]}
    assert_error(decode(packets), "tcp_acknowledges_uncaptured_data")


def t_record_truncated():
    packets = connection(req(False), nonstream())
    raw = pcap(packets)
    assert_error(decode_capture(raw[:-3], stderr(len(packets))), "pcap_record_data_truncated")


def t_snaplen_truncated():
    packets = connection(req(False), nonstream())
    raw = bytearray(pcap(packets))
    original = struct.unpack("<I", raw[36:40])[0]
    raw[36:40] = struct.pack("<I", original+5)
    assert_error(decode_capture(bytes(raw), stderr(len(packets))), "pcap_packet_truncated")


def t_drops():
    assert_error(decode(connection(req(False), nonstream()), drops=1), "pcap_drops")


def t_no_stats():
    packets = connection(req(False), nonstream())
    assert_error(decode_capture(pcap(packets), "tcpdump: listening on lo\n"),
                 "tcpdump_statistics_missing_or_ambiguous")


def t_bad_content_length():
    response = b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: 100\r\n\r\n{}"
    assert_error(decode(connection(req(False), response)), "http_content_length_truncated")


def t_missing_done():
    assert_error(decode(connection(req(True), chunked_response(SSE.replace(b"data: [DONE]\n\n", b"")))),
                 "sse_missing_done")


def t_unterminated_done():
    report = decode(connection(req(True), chunked_response(SSE[:-1])))
    assert_error(report, "sse_unterminated_event")
    assert report["exchanges"][0]["response"]["done"] is False


def t_unknown_dlt():
    assert_error(decode(connection(req(False), nonstream()), linktype=999), "linktype_unsupported")


def t_linktypes():
    for linktype in (113, 276, 0, 108, 101):
        assert_ok(decode(connection(req(False), nonstream()), linktype=linktype))


def t_big_endian_nano():
    report = decode(connection(req(False), nonstream()), endian=">", nano=True)
    assert_ok(report)
    assert report["metadata"]["pcap_timestamp_resolution"] == "nanoseconds"


def t_ipv6_unknown():
    packets = connection(req(False), nonstream())
    unknown = b"\x00"*12 + b"\x86\xdd" + b"\x60" + b"\x00"*39
    assert_error(decode(packets + [unknown]), "network_protocol_unsupported")


def t_close_delimited():
    body = b'{"id":"close","choices":[{"index":0,"message":{"role":"assistant","content":"ok"},"finish_reason":"stop"}]}'
    response = b"HTTP/1.0 200 OK\r\nContent-Type: application/json\r\n\r\n" + body
    report = decode(connection(req(False), response))
    assert_ok(report)
    assert report["exchanges"][0]["response"]["framing"] == "connection_close"
    assert_error(decode(connection(req(False), response, close=False)), "http_close_delimited_without_fin")


def t_conflicting_lengths():
    response = b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\nContent-Length: 3\r\n\r\n{}"
    assert_error(decode(connection(req(False), response)), "http_content_length_invalid")


def t_te_and_cl():
    response = chunked_response().replace(b"Transfer-Encoding: chunked", b"Transfer-Encoding: chunked\r\nContent-Length: 5")
    assert_error(decode(connection(req(True), response)), "http_ambiguous_framing")


def t_incomplete_chunk():
    assert_error(decode(connection(req(True), chunked_response()[:-5])), "http_chunk_size_truncated")


def t_seq_wrap():
    report = decode(connection(req(True), chunked_response(), cseq=0xFFFFFFF0, sseq=0xFFFFFFE0,
                               req_sizes=[8, 18, 22], resp_sizes=[7, 41, 16]))
    assert_ok(report)


def t_ancillary_and_cross_connection_order():
    get = b"GET /v1/models HTTP/1.1\r\nHost: 127.0.0.1:8000\r\n\r\n"
    body = b'{"data":[]}'
    response = b"HTTP/1.1 200 OK\r\nContent-Length: 11\r\nContent-Type: application/json\r\n\r\n" + body
    # Actual body is 11 bytes.
    assert len(body) == 11
    first = connection(get, response, client_port=41002)
    second = connection(req(False), nonstream(), client_port=41003)
    # Both connections start first; second's request is emitted first.
    packets = first[:3] + second[:3] + second[3:] + first[3:]
    report = decode(packets)
    assert_ok(report)
    assert [e["is_model_call"] for e in report["exchanges"]] == [True, False]
    assert report["metadata"]["http_exchange_count"] == 2 and report["metadata"]["model_call_count"] == 1


def t_syn_missing():
    packets = connection(req(False), nonstream())
    assert_error(decode(packets[1:]), "tcp_syn_missing")


def t_error_response():
    response = nonstream().replace(b"HTTP/1.1 200 OK", b"HTTP/1.1 500 Server Error")
    assert_error(decode(connection(req(False), response)), "model_http_error")


def t_interim():
    report = decode(connection(req(False), b"HTTP/1.1 100 Continue\r\n\r\n" + nonstream()))
    assert_ok(report)
    assert len(report["exchanges"][0]["interim_responses"]) == 1


def t_reset():
    packets = connection(req(False), nonstream(), close=False)
    packets.append(packet("s", 9001+len(nonstream()), 1001+len(req(False)), 20))
    assert_error(decode(packets), "tcp_reset")


def t_json_duplicate_key():
    body = b'{"model":"a","model":"b","stream":false}'
    request = b"POST /v1/chat/completions HTTP/1.1\r\nContent-Type: application/json\r\nContent-Length: " + str(len(body)).encode() + b"\r\n\r\n" + body
    assert_error(decode(connection(request, nonstream())), "json_duplicate_keys")


def t_complete_capture_noncomplete_window():
    report = decode(connection(req(False), nonstream(), close=False))
    assert_ok(report)
    assert report["metadata"]["capture_window_attestation_required"] is True


def main():
    for name, fn in [
        ("content_length_json_raw_preservation", t_json),
        ("chunked_sse_unicode_reasoning_raw_arguments_and_trailers", t_chunked),
        ("two_posts_keepalive", t_keepalive),
        ("out_of_order_and_consistent_retransmission", t_retransmit_out_of_order),
        ("overlap_conflict_rejected", t_overlap_conflict),
        ("missing_segment_rejected", t_gap),
        ("ack_reveals_missing_tail", t_missing_tail_ack),
        ("truncated_pcap_record", t_record_truncated),
        ("snaplen_truncation_rejected", t_snaplen_truncated),
        ("nonzero_kernel_drops_rejected", t_drops),
        ("missing_tcpdump_statistics_rejected", t_no_stats),
        ("truncated_content_length", t_bad_content_length),
        ("missing_sse_done", t_missing_done),
        ("unterminated_sse_done", t_unterminated_done),
        ("unknown_dlt_rejected", t_unknown_dlt),
        ("sll_sll2_null_loop_raw", t_linktypes),
        ("big_endian_nanosecond_pcap", t_big_endian_nano),
        ("unknown_ipv6_filtered_packet_rejected", t_ipv6_unknown),
        ("close_delimited_requires_fin", t_close_delimited),
        ("conflicting_content_length_rejected", t_conflicting_lengths),
        ("te_plus_cl_rejected", t_te_and_cl),
        ("missing_final_http_chunk", t_incomplete_chunk),
        ("tcp_sequence_wrap", t_seq_wrap),
        ("ancillary_http_and_cross_connection_request_order", t_ancillary_and_cross_connection_order),
        ("missing_syn_rejected", t_syn_missing),
        ("model_http_error_rejected", t_error_response),
        ("informational_response_pairing", t_interim),
        ("tcp_reset_rejected", t_reset),
        ("duplicate_json_key_rejected", t_json_duplicate_key),
        ("window_attestation_separate_from_byte_completeness", t_complete_capture_noncomplete_window),
    ]:
        test(name, fn)
    
    report = {"schema": "utcs_http_capture_selftest_v1", "run": 0, "fixtures": "in-memory synthetic only",
              "tests": RESULTS, "passed": sum(r["passed"] for r in RESULTS), "total": len(RESULTS),
              "all_pass": all(r["passed"] for r in RESULTS)}
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
