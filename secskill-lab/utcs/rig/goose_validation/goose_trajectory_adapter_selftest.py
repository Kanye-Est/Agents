#!/usr/bin/env python3
"""Offline synthetic adapter tests. No sockets, subprocesses, or model calls.

Each positive fixture is a real synthetic classic PCAP decoded by the sibling
http_capture.py, two HTTP model exchanges, hard-linked native logs, and a full
Goose-shaped session export. Negative cases alter one evidence invariant.
Temporary fixtures live only under this adapter directory and are removed.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import time
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import goose_trajectory_adapter as adapter
import http_capture
import http_capture_selftest as packet_fixture

CONSUMER=HERE.parents[1]/"trajectory_absence.py"
MODEL="qwen3-32b-awq-native-fc"
TOOL="utcs_mdclean__md_clean"
PROMPT="请整理 README。\n"
TEXT="#  A\r\n"
CLEAN="# A\n"
RAW_ARGS='{ "text": "\\u0023  A\\r\\n" }'
ARGS={"text":TEXT}

def dump(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

def native_message(role,blocks,identity=None):
    return {"id":identity,"role":role,"created":1700000000,"content":blocks,
            "metadata":{"userVisible":True,"agentVisible":True}}

def text_block(text):
    return {"type":"text","text":text}

def tool_request(identity="call_synthetic_1"):
    return {"type":"toolRequest","id":identity,
            "toolCall":{"status":"success","value":{"name":TOOL,"arguments":copy.deepcopy(ARGS)}}}

def tool_return(text=CLEAN):
    return {"type":"toolResponse","id":"call_synthetic_1",
            "toolResult":{"status":"success","value":{"content":[text_block(text)],"isError":False}}}

def make_request(payload):
    body=adapter.canonical(payload).encode("utf-8")
    return (b"POST /v1/chat/completions HTTP/1.1\r\nHost: 127.0.0.1:8000\r\n"
            b"Content-Type: application/json\r\nContent-Length: "+str(len(body)).encode()+b"\r\n\r\n"+body)

def response_chunks(identity,deltas):
    rows=[]
    for delta,finish in deltas:
        rows.append({"id":identity,"object":"chat.completion.chunk","model":MODEL,"created":1700000000,
                     "choices":[{"index":0,"delta":delta,"finish_reason":finish}]})
    rows.append({"id":identity,"object":"chat.completion.chunk","model":MODEL,"created":1700000000,
                 "choices":[],"usage":{"prompt_tokens":20,"completion_tokens":10,"total_tokens":30}})
    return rows

def response_bytes(chunks):
    body=("".join("data: "+adapter.canonical(row)+"\n\n" for row in chunks)+"data: [DONE]\n\n").encode("utf-8")
    return packet_fixture.chunked_response(body)

class Fixture:
    def __init__(self,root,*,nonstream=False,dual_reasoning=False):
        self.root=root
        self.logs=root/"native"
        self.original=root/"native-source"
        self.logs.mkdir()
        self.original.mkdir()
        self.prompt=root/"prompt.txt"
        self.prompt.write_bytes(PROMPT.encode())
        base={"model":MODEL,"stream":True,"stream_options":{"include_usage":True},"temperature":0,
              "messages":[{"role":"system","content":"Normal system."},
                          {"role":"developer","content":"Ordinary formatting task."},
                          {"role":"user","content":PROMPT}],
              "tools":[{"type":"function","function":{"name":TOOL,"description":"Normalize Markdown.",
                       "parameters":{"type":"object","properties":{"text":{"type":"string"}},
                                     "required":["text"],"additionalProperties":False}}}]}
        self.payloads=[copy.deepcopy(base),copy.deepcopy(base)]
        history_call={"id":"call_synthetic_1","type":"function","function":{"name":TOOL,
                       "arguments":adapter.canonical(ARGS)}}
        self.payloads[1]["messages"].extend([
            {"role":"assistant","content":"先整理。","tool_calls":[history_call]},
            {"role":"tool","tool_call_id":"call_synthetic_1","content":CLEAN}])
        deltas0=[
            ({"role":"assistant","reasoning_content":"检查"},None),
            ({"reasoning_content":"格式"},None),
            ({"content":"先整理。"},None),
            ({"tool_calls":[{"index":0,"id":"call_synthetic_1","type":"function",
                             "function":{"name":TOOL,"arguments":RAW_ARGS[:12]}}]},None),
            ({"tool_calls":[{"index":0,"function":{"arguments":RAW_ARGS[12:]}}]},"tool_calls"),
        ]
        if dual_reasoning:
            deltas0[0][0]["reasoning"]="fallback exposed"
        deltas1=[({"role":"assistant","content":"# "},None),({"content":"A\n"},"stop")]
        self.chunks=[response_chunks("chatcmpl-synthetic-0",deltas0),
                     response_chunks("chatcmpl-synthetic-1",deltas1)]
        self.responses=[response_bytes(rows) for rows in self.chunks]
        if nonstream:
            for payload in self.payloads:
                payload["stream"]=False
                del payload["stream_options"]
            messages=[
                {"role":"assistant","content":"先整理。","reasoning_content":"检查格式",
                 "tool_calls":[{"id":"call_synthetic_1","type":"function",
                                "function":{"name":TOOL,"arguments":RAW_ARGS}}]},
                {"role":"assistant","content":CLEAN},
            ]
            self.responses=[]
            for i,message in enumerate(messages):
                result={"id":f"chatcmpl-synthetic-{i}","model":MODEL,"object":"chat.completion",
                        "choices":[{"index":0,"message":message,"finish_reason":"tool_calls" if i==0 else "stop"}],
                        "usage":{"prompt_tokens":20,"completion_tokens":10,"total_tokens":30}}
                body=adapter.canonical(result).encode()
                self.responses.append(b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: "+
                                      str(len(body)).encode()+b"\r\n\r\n"+body)
        self.wire_path=root/"wire.json"
        self.pcap=root/"capture.pcap"
        self.stderr=root/"tcpdump.stderr"
        self.build_wire()
        self.native_rows=[
            [{"data":native_message("assistant",[{"type":"thinking","thinking":"检查格式","signature":""}]),"usage":None},
             {"data":native_message("assistant",[text_block("先整理。")]),"usage":None},
             {"data":native_message("assistant",[tool_request()]),"usage":None},
             {"data":None,"usage":{"input_tokens":20,"output_tokens":10,"total_tokens":30}}],
            [{"data":native_message("assistant",[text_block("# ")]),"usage":None},
             {"data":native_message("assistant",[text_block("A\n")]),"usage":None},
             {"data":None,"usage":{"input_tokens":20,"output_tokens":10,"total_tokens":30}}],
        ]
        for i in range(2):
            source=self.original/f"request-{i}.jsonl"
            target=self.logs/f"preserved-{i}.jsonl"
            rows=[{"model_config":{"model_name":MODEL},"input":self.payloads[i]}]+self.native_rows[i]
            source.write_text("".join(adapter.canonical(row)+"\n" for row in rows),encoding="utf-8")
            os.link(source,target)
        self.session_path=root/"session.json"
        self.session={"id":"synthetic-session","provider_name":"openai","model_config":{"model_name":MODEL},
                      "message_count":4,"conversation":[
                          native_message("user",[text_block(PROMPT)],"message-0"),
                          native_message("assistant",[{"type":"thinking","thinking":"检查格式","signature":""},
                                         text_block("先整理。"),tool_request()],"message-1"),
                          native_message("user",[tool_return()],"message-2"),
                          native_message("assistant",[text_block(CLEAN)],"message-3")]}
        dump(self.session_path,self.session)
        self.completion_path=root/"completion.json"
        self.meta={"schema":"utcs_goose_capture_completion_v1","goose_version":"1.45.0","expected_model":MODEL,
                   "goose":{"started_ns":1699999999900000000,"finished_ns":1700000001000000000,
                            "exit_code":0,"session_id":"synthetic-session"},
                   "capture":{"ready_ns":1699999999800000000,"finished_ns":1700000002000000000,"exit_code":0},
                   "watcher":{"ready_ns":1699999999800000000,"finished_ns":1700000002000000000,"exit_code":0,
                              "initial_source_files":[],"final_scan_complete":True,"errors":[],"files":[]},
                   "prompt":{"path":str(self.prompt),"sha256":adapter.sha(self.prompt.read_bytes())}}
        self.refresh_inventory()
    def build_wire(self):
        packets=[]
        for i in range(2):
            packets+=packet_fixture.connection(make_request(self.payloads[i]),self.responses[i],
                        client_port=41001+i,req_sizes=[31,97],resp_sizes=[17,109,503])
        self.pcap.write_bytes(packet_fixture.pcap(packets))
        self.stderr.write_text(packet_fixture.stderr(len(packets)),encoding="utf-8")
        self.wire=http_capture.decode_capture(self.pcap.read_bytes(),self.stderr.read_bytes(),
                              pcap_path=str(self.pcap),tcpdump_stderr_path=str(self.stderr))
        assert self.wire["complete"],self.wire["errors"]
        dump(self.wire_path,self.wire)
    def refresh_inventory(self):
        entries=[]
        for path in sorted(self.logs.iterdir()):
            info=path.stat()
            entries.append({"path":str(path),"sha256":adapter.sha(path.read_bytes()),
                            "device":info.st_dev,"inode":info.st_ino})
        self.meta["watcher"]["files"]=entries
        dump(self.completion_path,self.meta)
    def edit_meta(self,fn):
        fn(self.meta)
        dump(self.completion_path,self.meta)
    def edit_session(self,fn):
        fn(self.session)
        dump(self.session_path,self.session)
    def edit_wire(self,fn):
        fn(self.wire)
        dump(self.wire_path,self.wire)
    def edit_native(self,index,fn):
        path=self.logs/f"preserved-{index}.jsonl"
        rows=[json.loads(line) for line in path.read_text().splitlines()]
        fn(rows)
        path.write_text("".join(adapter.canonical(row)+"\n" for row in rows),encoding="utf-8")
        self.refresh_inventory()
    def run(self):
        return adapter.adapt(self.wire_path,self.logs,self.session_path,self.completion_path,CONSUMER)

CASES=[]
def case(name,fn):
    CASES.append((name,fn))

def passes(f):
    trajectory,manifest,text=f.run()
    assert trajectory["capture_complete"] is True,manifest["errors"]
    assert manifest["errors"]==[]
    assert manifest["model_call_count"]==2
    assert manifest["generated_tool_call_count"]==1
    assert manifest["consumer_structural_validation"]["ok"] is True
    assert manifest["scope"]["trajectory_absent_assessed"] is False
    return trajectory,manifest,text

def fails(f,code=None):
    trajectory,manifest,_=f.run()
    assert trajectory["capture_complete"] is False,manifest
    assert manifest["errors"],manifest
    if code:
        assert code in {e["code"] for e in manifest["errors"]},manifest["errors"]
    return trajectory,manifest

def positive_all_sources(f):
    trajectory,manifest,text=passes(f)
    assert set(e["source"] for e in trajectory["events"])==set(adapter.SOURCES)
    generated=[e for e in trajectory["events"] if e["source"]=="tool_call_request"
               and e.get("evidence_kind")=="model_response"]
    assert generated[0]["tool"]==TOOL and generated[0]["args"]==ARGS
    assert generated[0]["raw_arguments"]==RAW_ARGS
    assert RAW_ARGS in text and "检查" in text and "格式" in text
    assert any(e.get("content_kind")=="api_tools_schema" for e in trajectory["events"])
    assert all(type(e["seq"]) is int for e in trajectory["events"])
    assert manifest["normalized_T_sha256"]==adapter.sha(text.encode())
case("complete_streaming_pipeline_all_seven_sources_raw_args",positive_all_sources)

def deterministic(f):
    first=f.run()
    second=f.run()
    assert first==second
case("byte_deterministic_repeat_adaptation",deterministic)

def missing_log(f):
    (f.logs/"preserved-0.jsonl").unlink()
    fails(f,"request_log_stat_failed")
case("missing_preserved_log_refused",missing_log)

def missing_wire_call(f):
    f.edit_wire(lambda w:w["exchanges"].pop())
    fails(f,"native_wire_request_count_mismatch")
case("missing_http_exchange_refused",missing_wire_call)

def missing_session(f):
    f.edit_session(lambda s:s["conversation"].pop())
    fails(f,"session_message_count_mismatch")
case("truncated_session_refused",missing_session)

def bad_hash(f):
    f.edit_meta(lambda m:m["watcher"]["files"][0].update(sha256="0"*64))
    fails(f,"source_sha256_mismatch")
case("native_hash_mismatch_refused",bad_hash)

def bad_inode(f):
    f.edit_meta(lambda m:m["watcher"]["files"][0].update(inode=0))
    fails(f,"request_log_inode_mismatch")
case("hardlink_inode_mismatch_refused",bad_inode)

def extra_file(f):
    (f.logs/"unlisted.jsonl").write_text("{}\n")
    fails(f,"request_log_inventory_mismatch")
case("unlisted_log_refused",extra_file)

def dup_entry(f):
    f.edit_meta(lambda m:m["watcher"]["files"].append(copy.deepcopy(m["watcher"]["files"][0])))
    fails(f,"duplicate_preserved_inode")
case("duplicate_preserved_inode_refused",dup_entry)

def bad_times(f):
    f.edit_meta(lambda m:m["capture"].update(ready_ns=m["goose"]["started_ns"]+1))
    fails(f,"capture_does_not_enclose_goose")
case("capture_started_late_refused",bad_times)

def bad_watcher(f):
    f.edit_meta(lambda m:m["watcher"].update(final_scan_complete=False))
    fails(f,"watcher_final_scan_incomplete")
case("watcher_not_finalized_refused",bad_watcher)

def watcher_error(f):
    f.edit_meta(lambda m:m["watcher"].update(errors=[{"code":"inotify_overflow"}]))
    fails(f,"watcher_errors")
case("watcher_error_refused",watcher_error)

def nonempty_initial(f):
    f.edit_meta(lambda m:m["watcher"].update(initial_source_files=["old.jsonl"]))
    fails(f,"request_directory_not_initially_empty")
case("preexisting_request_logs_refused",nonempty_initial)

def failed_process(f):
    f.edit_meta(lambda m:m["goose"].update(exit_code=1))
    fails(f,"process_not_successful")
case("goose_failure_refused",failed_process)

def false_attestation(f):
    f.edit_wire(lambda w:w.update(complete=False,errors=[{"code":"tcp_gap"}]))
    fails(f,"wire_capture_incomplete")
case("upstream_capture_incomplete_refused",false_attestation)

def fabricated_projection(f):
    f.edit_wire(lambda w:w["metadata"].update(packet_count=999))
    fails(f,"wire_projection_differs_from_pcap")
case("wire_projection_must_rederive_from_actual_pcap",fabricated_projection)

def duplicate_exchange(f):
    f.edit_wire(lambda w:w["exchanges"].append(copy.deepcopy(w["exchanges"][0])))
    fails(f,"duplicate_exchange_id")
case("duplicate_exchange_id_refused",duplicate_exchange)

def raw_log_duplicate_json(f):
    path=f.logs/"preserved-0.jsonl"
    text=path.read_text()
    text=text.replace('"model_config":','"input":{},"model_config":',1)
    path.write_text(text)
    f.refresh_inventory()
    fails(f,"invalid_json")
case("duplicate_json_key_in_native_log_refused",raw_log_duplicate_json)

def log_truncate(f):
    path=f.logs/"preserved-0.jsonl"
    path.write_bytes(path.read_bytes().rstrip(b"\n"))
    f.refresh_inventory()
    fails(f,"native_log_truncated")
case("native_partial_final_line_refused",log_truncate)

def native_output_disagrees(f):
    f.edit_native(1,lambda rows:rows[1]["data"]["content"][0].update(text="MISMATCH"))
    fails(f,"native_response_semantics_mismatch")
case("native_response_crosscheck_refuses_changed_output",native_output_disagrees)

def native_error(f):
    f.edit_native(0,lambda rows:rows.append({"error":"synthetic provider failure"}))
    fails(f,"unknown_fields")
case("native_provider_error_refused",native_error)

def unknown_session_content(f):
    f.edit_session(lambda s:s["conversation"][3]["content"].append(
        {"type":"unknownFutureBlock","text":"unknown"}))
    fails(f,"unknown_native_content_block")
case("unknown_native_block_refused",unknown_session_content)

def tool_error(f):
    f.edit_session(lambda s:s["conversation"][2]["content"][0]["toolResult"]["value"].update(isError=True))
    fails(f,"native_tool_execution_error")
case("tool_result_error_refused",tool_error)

def duplicate_session_ids(f):
    f.edit_session(lambda s:s["conversation"][3].update(id="message-0"))
    fails(f,"duplicate_session_message_id")
case("duplicate_session_message_id_refused",duplicate_session_ids)

def missing_return(f):
    f.edit_session(lambda s:s["conversation"][2].update(content=[]))
    fails(f,"session_tool_returns_mismatch")
case("missing_tool_result_crosscheck_refused",missing_return)

def changed_prompt(f):
    f.prompt.write_text("Different prompt\n")
    f.edit_meta(lambda m:m["prompt"].update(sha256=adapter.sha(f.prompt.read_bytes())))
    fails(f,"frozen_prompt_not_exact_wire_user")
case("actual_wire_prompt_must_match_frozen_bytes",changed_prompt)

def native_tool_name_changed(f):
    f.edit_native(0,lambda rows:rows[3]["data"]["content"][0]["toolCall"]["value"].update(name="wrong_tool"))
    fails(f,"native_response_semantics_mismatch")
case("tool_full_name_mismatch_refused",native_tool_name_changed)

def wire_unknown_block(f):
    f.chunks[1][0]["choices"][0]["delta"]["future_block"]={"text":"unhandled"}
    f.responses[1]=response_bytes(f.chunks[1])
    f.build_wire()
    fails(f,"unknown_fields")
case("unknown_backend_field_refused",wire_unknown_block)

def wire_truncated_finish(f):
    f.chunks[1][-2]["choices"][0]["finish_reason"]="length"
    f.responses[1]=response_bytes(f.chunks[1])
    f.build_wire()
    fails(f,"truncated_or_unknown_finish")
case("length_finish_refused",wire_truncated_finish)

def duplicate_completion(f):
    for row in f.chunks[1]:
        row["id"]="chatcmpl-synthetic-0"
    f.responses[1]=response_bytes(f.chunks[1])
    f.build_wire()
    fails(f,"duplicate_completion_id")
case("duplicate_completion_id_refused",duplicate_completion)

def raw_arguments_invalid(f):
    f.chunks[0][3]["choices"][0]["delta"]["tool_calls"][0]["function"]["arguments"]="{bad"
    f.chunks[0][4]["choices"][0]["delta"]["tool_calls"][0]["function"]["arguments"]="}"
    f.responses[0]=response_bytes(f.chunks[0])
    f.build_wire()
    fails(f,"invalid_json")
case("invalid_tool_arguments_refused",raw_arguments_invalid)

def request_outside_window(f):
    f.edit_meta(lambda m:m["goose"].update(finished_ns=1699999999950000000))
    fails(f,"model_request_outside_goose_window")
case("model_request_timestamp_bound_to_goose_window",request_outside_window)

def named_message_preserved(f):
    for index,payload in enumerate(f.payloads):
        payload["messages"][2]["name"]="SYNTHETIC-NAMED-SPEAKER"
        f.edit_native(index,lambda rows,payload=payload:rows[0].update(input=payload))
    f.build_wire()
    _,_,text=passes(f)
    assert "SYNTHETIC-NAMED-SPEAKER" in text
case("permitted_message_metadata_is_retained_in_T",named_message_preserved)

def missing_final_native_usage(f):
    f.edit_native(1,lambda rows:rows.pop())
    fails(f,"native_final_usage_missing")
case("native_complete_text_but_missing_final_usage_refused",missing_final_native_usage)

def missing_required_digest(f):
    f.edit_meta(lambda m:m["watcher"]["files"][0].pop("sha256"))
    fails(f,"request_log_hash_missing")
case("missing_required_log_hash_refused",missing_required_digest)

def missing_prompt_digest(f):
    f.edit_meta(lambda m:m["prompt"].pop("sha256"))
    fails(f,"frozen_prompt_hash_missing")
case("missing_frozen_prompt_hash_refused",missing_prompt_digest)

def missing_expected_model(f):
    f.edit_meta(lambda m:m.pop("expected_model"))
    fails(f,"expected_model_missing")
case("missing_expected_model_identity_refused",missing_expected_model)

def rewrite_backend_response(f,index,edit):
    streaming=f.payloads[index]["stream"]
    if streaming:
        rows=f.chunks[index]
    else:
        rows=[json.loads(f.responses[index].split(b"\r\n\r\n",1)[1])]
    edit(rows)
    if streaming:
        f.responses[index]=response_bytes(rows)
    else:
        body=adapter.canonical(rows[0]).encode("utf-8")
        f.responses[index]=(b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: "+
                            str(len(body)).encode()+b"\r\n\r\n"+body)
    f.build_wire()
    return copy.deepcopy(rows)

def backend_metadata_roundtrip(f,nulls):
    expected=[]
    for response_index in range(2):
        def edit(rows):
            rows[0]["prompt_token_ids"]=None if nulls else ([0,151643] if response_index==0 else [])
            for chunk_index,row in enumerate(rows):
                for choice in row["choices"]:
                    choice["token_ids"]=None if nulls else ([151645,0] if (response_index+chunk_index)%2 else [])
                    if choice.get("finish_reason") is not None:
                        choice["stop_reason"]=None if nulls else (0 if response_index==0 else "SYNTHETIC-STOP-\n终止")
        expected.append(rewrite_backend_response(f,response_index,edit))
    trajectory,_,text=passes(f)
    for response_index,rows in enumerate(expected):
        envelopes=[event for event in trajectory["events"]
                   if event.get("content_kind")=="wire_response_envelope"
                   and event.get("request_ordinal")==response_index]
        assert [json.loads(event["content"]) for event in envelopes]==rows
        assert all(adapter.canonical(row) in text for row in rows)
        assert "prompt_token_ids" in json.loads(envelopes[0]["content"])
        assert any("token_ids" in choice for row in rows for choice in row["choices"])
        assert any("stop_reason" in choice for row in rows for choice in row["choices"])
case("vllm_sse_null_metadata_retained_in_envelope_and_T",lambda f:backend_metadata_roundtrip(f,True))
case("vllm_sse_nonnull_metadata_retained_in_envelope_and_T",lambda f:backend_metadata_roundtrip(f,False))

def backend_metadata_rejected(f,location,field,value,code):
    def edit(rows):
        target=rows[0]
        if location=="choice":
            target=target["choices"][0]
        elif location=="delta":
            target=target["choices"][0]["delta" if f.payloads[1]["stream"] else "message"]
        target[field]=copy.deepcopy(value)
    rows=rewrite_backend_response(f,1,edit)
    trajectory,_=fails(f,code)
    envelopes=[event for event in trajectory["events"]
               if event.get("content_kind")=="wire_response_envelope"
               and event.get("request_ordinal")==1]
    # Rejection must not discard the unknown or malformed value from evidence.
    assert [json.loads(event["content"]) for event in envelopes]==rows

for location,field in (("top","prompt_token_ids"),("choice","token_ids")):
    for kind,value in (("scalar",5),("string","5"),("object",{"id":5}),
                       ("boolean_element",[True]),("float_element",[5.0]),("null_element",[None])):
        case(f"vllm_{field}_{kind}_refused",
             lambda f,location=location,field=field,value=value:
                 backend_metadata_rejected(f,location,field,value,"token_ids_type_invalid"))
for kind,value in (("boolean",True),("float",5.0),("object",{"reason":"stop"}),("array",[5])):
    case(f"vllm_stop_reason_{kind}_refused",
         lambda f,value=value:backend_metadata_rejected(f,"choice","stop_reason",value,"stop_reason_type_invalid"))
for location,field,value in (("choice","prompt_token_ids",[5]),("top","token_ids",[5]),
                             ("delta","stop_reason","SYNTHETIC-STOP")):
    case(f"vllm_{field}_wrong_layer_refused",
         lambda f,location=location,field=field,value=value:
             backend_metadata_rejected(f,location,field,value,"unknown_fields"))
case("unknown_top_level_null_field_still_refused",
     lambda f:backend_metadata_rejected(f,"top","future_metadata",None,"unknown_fields"))
case("unknown_choice_nonnull_field_still_refused",
     lambda f:backend_metadata_rejected(f,"choice","future_metadata",{"unhandled":"SYNTHETIC"},"unknown_fields"))

def nonstream_metadata(fn):
    with tempfile.TemporaryDirectory(prefix="goose-adapter-selftest-",dir=HERE) as directory:
        fn(Fixture(Path(directory),nonstream=True))

def final_thinking_cross_chunk(f, field):
    marker="UTCS-SYNTHETIC-CROSS-CHUNK-MARKER"
    pieces=["UTCS-SYNTHETIC-CROSS-", "CHUNK-MARKER"]
    assert all(marker not in piece for piece in pieces)
    for index,piece in enumerate(pieces):
        f.chunks[1][index]["choices"][0]["delta"][field]=piece
    f.responses[1]=response_bytes(f.chunks[1])
    f.build_wire()
    def update_rows(rows):
        for index,piece in enumerate(pieces,1):
            rows[index]["data"]["content"].insert(0,{"type":"thinking","thinking":piece,"signature":""})
    f.edit_native(1,update_rows)
    f.edit_session(lambda s:s["conversation"][3]["content"].insert(
        0,{"type":"thinking","thinking":marker,"signature":""}))
    trajectory,manifest,text=passes(f)
    assembled=[event for event in trajectory["events"]
               if event["source"]=="thinking"
               and event.get("content_kind")=="assembled_backend_thinking"
               and event.get("request_ordinal")==1 and event.get("wire_field")==field]
    assert len(assembled)==1
    assert assembled[0]["content"]==marker
    assert len(assembled[0]["stream_chunks"])==2
    assert marker in text
    assert len(manifest["model_calls"])==2
    fragments=[event for event in trajectory["events"]
               if event["source"]=="thinking"
               and event.get("content_kind")=="backend_thinking_fragment"
               and event.get("request_ordinal")==1 and event.get("wire_field")==field]
    assert [event["content"] for event in fragments]==pieces
    # This is the final response: no next request history can incidentally repair it.
    assert not any(event.get("request_ordinal",0)>1 for event in trajectory["events"])
case("final_turn_reasoning_content_cross_chunk_marker_contiguous",
     lambda f:final_thinking_cross_chunk(f,"reasoning_content"))
case("final_turn_reasoning_cross_chunk_marker_contiguous",
     lambda f:final_thinking_cross_chunk(f,"reasoning"))

def both_reasoning_fields():
    with tempfile.TemporaryDirectory(prefix="goose-adapter-selftest-",dir=HERE) as directory:
        f=Fixture(Path(directory),dual_reasoning=True)
        _,_,text=passes(f)
        assert "fallback exposed" in text
        assert "检查" in text
        return None

def nonstreaming():
    with tempfile.TemporaryDirectory(prefix="goose-adapter-selftest-",dir=HERE) as directory:
        f=Fixture(Path(directory),nonstream=True)
        passes(f)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,
                        default=HERE/"validation"/"goose_trajectory_adapter_selftest.result.json")
    args=parser.parse_args()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    report={"schema":"utcs_goose_adapter_selftest_v1","synthetic_only":True,
            "model_calls_executed":0,"network_calls_executed":0,"run":0,"tests":[]}
    for name,fn in CASES:
        try:
            with tempfile.TemporaryDirectory(prefix="goose-adapter-selftest-",dir=HERE) as directory:
                fixture=Fixture(Path(directory))
                fn(fixture)
            report["tests"].append({"name":name,"passed":True})
            print("[PASS]",name)
        except Exception as error:
            report["tests"].append({"name":name,"passed":False,"error":repr(error)})
            print("[FAIL]",name,repr(error))
    for name,fn in (("both_backend_reasoning_fields_retained",both_reasoning_fields),
                    ("complete_nonstream_json_pipeline",nonstreaming),
                    ("vllm_json_null_metadata_retained_in_envelope_and_T",
                     lambda:nonstream_metadata(lambda f:backend_metadata_roundtrip(f,True))),
                    ("vllm_json_nonnull_metadata_retained_in_envelope_and_T",
                     lambda:nonstream_metadata(lambda f:backend_metadata_roundtrip(f,False))),
                    ("vllm_json_prompt_token_ids_boolean_refused",
                     lambda:nonstream_metadata(lambda f:backend_metadata_rejected(f,"top","prompt_token_ids",[False],"token_ids_type_invalid"))),
                    ("vllm_json_token_ids_float_refused",
                     lambda:nonstream_metadata(lambda f:backend_metadata_rejected(f,"choice","token_ids",[3.0],"token_ids_type_invalid"))),
                    ("vllm_json_stop_reason_object_refused",
                     lambda:nonstream_metadata(lambda f:backend_metadata_rejected(f,"choice","stop_reason",{},"stop_reason_type_invalid")))):
        try:
            fn()
            report["tests"].append({"name":name,"passed":True})
            print("[PASS]",name)
        except Exception as error:
            report["tests"].append({"name":name,"passed":False,"error":repr(error)})
            print("[FAIL]",name,repr(error))
    report["passed"]=sum(r["passed"] for r in report["tests"])
    report["total"]=len(report["tests"])
    report["all_pass"]=report["passed"]==report["total"]
    report["adapter_sha256"]=adapter.sha((HERE/"goose_trajectory_adapter.py").read_bytes())
    report["selftest_sha256"]=adapter.sha(Path(__file__).read_bytes())
    report["http_decoder_sha256"]=adapter.sha((HERE/"http_capture.py").read_bytes())
    report["consumer_sha256"]=adapter.sha(CONSUMER.read_bytes())
    dump(args.output,report)
    print(json.dumps({key:report[key] for key in ("all_pass","passed","total","synthetic_only","run")}))
    return 0 if report["all_pass"] else 1

if __name__=="__main__":
    raise SystemExit(main())
