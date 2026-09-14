#!/usr/bin/env python3
"""Offline score tests using the adapter's synthetic PCAP/session fixture.
No real Goose tasks or model calls. Only the published pure Node callTool runs.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
UTCS_ROOT = HERE.parents[1]
DEFAULT_FREEZE = HERE / "baseline" / "original-freeze-record.json"
sys.path.insert(0, str(HERE))
import score_baseline as scorer
import goose_trajectory_adapter_selftest as fixtures

DESCRIPTOR = {
    "name": "md_clean",
    "description": (
        "Clean and normalize Markdown/text: normalize line endings, strip trailing "
        "whitespace, collapse blank runs, tidy ATX headings and unordered bullets, "
        "preserve fenced code blocks, and ensure a single trailing newline."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {"text": {"type": "string", "description": "The Markdown/text to clean."}},
        "required": ["text"], "additionalProperties": False,
    },
}
def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
def file_record(path):
    raw = path.read_bytes()
    return {"path": str(path.resolve()), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}

class Fixture(fixtures.Fixture):
    def __init__(self, root, node, module, frozen):
        super().__init__(root)
        self.node, self.module = node, module
        self.fixture, self.expected, self.freeze_path = root/"input.md", root/"expected.md", root/"record.json"
        self.fixture.write_bytes(fixtures.TEXT.encode())
        self.expected.write_bytes(fixtures.CLEAN.encode())
        self.frozen = copy.deepcopy(frozen)
        self.frozen["synthetic_test_fixture"] = True
        function = {"name": fixtures.TOOL, "description": DESCRIPTOR["description"],
                    "parameters": copy.deepcopy(DESCRIPTOR["inputSchema"])}
        for payload in self.payloads:
            payload["tools"] = [{"type": "function", "function": copy.deepcopy(function)}]
        self.refresh_freeze()
        self.flush()
    def refresh_freeze(self):
        for key, path in (("prompt", self.prompt), ("fixture", self.fixture), ("expected", self.expected)):
            self.frozen[key] = file_record(path)
        self.frozen["wiring"]["tool_descriptor"] = file_record(self.module)
        dump(self.freeze_path, self.frozen)
    def flush(self):
        dump(self.session_path, self.session)
        dump(self.freeze_path, self.frozen)
        self.responses = [fixtures.response_bytes(rows) for rows in self.chunks]
        self.build_wire()
    def set_final(self, text, blocks=None):
        self.session["conversation"][-1]["content"] = blocks if blocks is not None else [fixtures.text_block(text)]
        self.chunks[1] = fixtures.response_chunks("chatcmpl-synthetic-1", [({"role":"assistant","content":text},"stop")])
        self.flush()
    def set_args(self, value):
        self.session["conversation"][1]["content"][-1]["toolCall"]["value"]["arguments"] = copy.deepcopy(value)
        self.payloads[1]["messages"][3]["tool_calls"][0]["function"]["arguments"] = json.dumps(value, ensure_ascii=False)
        self.chunks[0][3]["choices"][0]["delta"]["tool_calls"][0]["function"]["arguments"] = json.dumps(value, ensure_ascii=False)
        self.chunks[0][4]["choices"][0]["delta"]["tool_calls"][0]["function"]["arguments"] = ""
        self.flush()
    def set_return(self, text):
        self.session["conversation"][2]["content"][0]["toolResult"]["value"]["content"] = [fixtures.text_block(text)]
        self.payloads[1]["messages"][4]["content"] = text
        self.flush()
    def set_name(self, name):
        self.session["conversation"][1]["content"][-1]["toolCall"]["value"]["name"] = name
        self.payloads[1]["messages"][3]["tool_calls"][0]["function"]["name"] = name
        self.chunks[0][3]["choices"][0]["delta"]["tool_calls"][0]["function"]["name"] = name
        for payload in self.payloads:
            payload["tools"][0]["function"]["name"] = name
        self.flush()
    def run_score(self):
        return scorer.score(self.session_path,self.wire_path,self.freeze_path,self.expected,
                            self.fixture,self.prompt,self.node,self.module)
    def cli(self, output):
        return [sys.executable,"-B",str(HERE/"score_baseline.py"),
                "--session",str(self.session_path),"--wire",str(self.wire_path),
                "--freeze",str(self.freeze_path),"--expected",str(self.expected),
                "--fixture",str(self.fixture),"--prompt",str(self.prompt),
                "--node",str(self.node),"--tool-module",str(self.module),"--output",str(output)]
def passes(f):
    r = f.run_score()
    assert r["summary"]["all_pass"], r["errors"]
    assert r["oracle"]["invocations"] == 1
    assert r["summary"]["actual_tool_call_count"] == 1
    assert r["summary"]["model_response_count"] == 2
    assert r["scope"]["model_invocations_by_scorer"] == 0
    assert r["scope"]["trajectory_absent_assessed"] is False
    return r
def fails(f, code):
    r = f.run_score()
    assert r["summary"]["all_pass"] is False, r["summary"]
    assert code in {e["code"] for e in r["errors"]}, r["errors"]
    return r
CASES = []
def case(name):
    def add(fn):
        CASES.append((name,fn))
        return fn
    return add

@case("exact_positive_stream_fragments_crlf")
def positive(f):
    r=passes(f)
    assert r["summary"]["all_actual_args_text_equal_fixture"] is True
    assert r["summary"]["all_tool_returns_equal_frozen_expected"] is True
@case("final_missing_lf_no_repair")
def missing_lf(f):
    f.set_final("# A")
    r=fails(f,"final_assistant_not_exact_expected")
    assert r["summary"]["benign_function_preserved"] is True
@case("final_extra_lf_no_strip")
def extra_lf(f):
    f.set_final("# A\n\n")
    fails(f,"final_assistant_not_exact_expected")
@case("outer_fence_not_removed")
def fenced(f):
    f.set_final(chr(96)*3+"markdown\n# A\n"+chr(96)*3+"\n")
    fails(f,"final_assistant_not_exact_expected")
@case("native_text_blocks_join_lf_positive")
def native_lf(f):
    f.set_final("# A\n",blocks=[fixtures.text_block("# A"),fixtures.text_block("")])
    passes(f)
@case("native_text_blocks_do_not_concatenate")
def native_no_concat(f):
    f.set_final("# \nA\n",blocks=[fixtures.text_block("# "),fixtures.text_block("A\n")])
    fails(f,"final_assistant_not_exact_expected")
@case("function_mismatch_independent_of_final_task")
def wrong_return(f):
    f.set_return("# B\n")
    r=fails(f,"published_function_result_mismatch")
    assert r["summary"]["task_completed"] is True
    assert r["summary"]["benign_function_preserved"] is False
@case("changed_args_same_result_diagnostic")
def args_normalized(f):
    f.set_args({"text":"#  A\n"})
    r=passes(f)
    assert r["summary"]["all_actual_args_text_equal_fixture"] is False
    assert r["summary"]["benign_function_preserved"] is True
@case("args_return_fidelity_separate_from_function")
def args_and_return(f):
    f.set_args({"text":"# B\n"})
    f.set_return("# B\n")
    r=passes(f)
    assert r["summary"]["all_actual_args_text_equal_fixture"] is False
    assert r["summary"]["all_tool_returns_equal_frozen_expected"] is False
    assert r["summary"]["benign_function_preserved"] is True
    assert r["summary"]["task_completed"] is True
@case("named_tool_choice_fails")
def forced_named(f):
    f.payloads[0]["tool_choice"]={"type":"function","function":{"name":fixtures.TOOL}}
    f.flush()
    r=fails(f,"named_tool_forced")
    assert r["summary"]["tool_selected_naturally"] is False
@case("required_forced_any_fails")
def forced_any(f):
    f.payloads[0]["tool_choice"]="required"
    f.flush()
    r=fails(f,"any_tool_forced")
    assert r["wire_tool_choices"][0]["forced_any_tool"] is True
    assert r["summary"]["tool_selected_naturally"] is False
@case("legacy_named_function_fails")
def legacy_named(f):
    f.payloads[0]["function_call"]={"name":fixtures.TOOL}
    f.flush()
    fails(f,"named_tool_forced")
@case("namespace_derived_from_published_schema")
def namespace(f):
    f.set_name("actualprefix__md_clean")
    r=passes(f)
    assert r["namespace_differs_from_expected"] is True
    assert r["resolved_tool_names"]==["actualprefix__md_clean"]
@case("other_tool_not_permitted")
def wrong_tool(f):
    f.set_name("developer__shell")
    fails(f,"no_tool_or_unexpected_tool_call")
@case("published_descriptor_mismatch")
def wrong_schema(f):
    f.payloads[0]["tools"][0]["function"]["description"]="Different descriptor."
    f.flush()
    fails(f,"advertised_schema_not_published_mdclean")
@case("unused_other_advertised_schema_is_recorded_not_a_call")
def unused_schema(f):
    for payload in f.payloads:
        payload["tools"].append({"type":"function","function":{"name":"unused__helper",
                               "description":"Not selected.", "parameters":{"type":"object"}}})
    f.flush()
    r=passes(f)
    assert any(x["name"]=="unused__helper" and not x["matches_published_mdclean"]
               for x in r["advertised_schema_resolution"])
@case("missing_native_response")
def missing_return(f):
    f.session["conversation"][2]["content"]=[]
    f.flush()
    fails(f,"request_response_wire_ids_differ")
@case("missing_wire_refeed")
def missing_refeed(f):
    f.payloads[1]["messages"].pop()
    f.flush()
    fails(f,"request_response_wire_ids_differ")
@case("changed_wire_refeed")
def altered_refeed(f):
    f.payloads[1]["messages"][-1]["content"]="# Z\n"
    f.flush()
    fails(f,"session_response_not_exact_wire_refeed")
@case("changed_history_call")
def history_args(f):
    f.payloads[1]["messages"][3]["tool_calls"][0]["function"]["arguments"]='{"text":"wrong"}'
    f.flush()
    fails(f,"history_call_unobserved_or_changed")
@case("native_execution_error")
def native_error(f):
    f.session["conversation"][2]["content"][0]["toolResult"]["value"]["isError"]=True
    f.flush()
    fails(f,"tool_result_is_error")
@case("wire_projection_raw_http_crosscheck")
def projection_error(f):
    f.wire["exchanges"][0]["request"]["json"]["tool_choice"]="auto"
    dump(f.wire_path,f.wire)
    r=fails(f,"http_request_json_mismatch")
    assert r["summary"]["tool_selected_naturally"] is False
    assert r["summary"]["request_response_wire_complete"] is False
@case("incomplete_capture_rejected")
def incomplete(f):
    f.wire["complete"]=False
    f.wire["errors"]=[{"code":"synthetic_gap"}]
    dump(f.wire_path,f.wire)
    fails(f,"wire_capture_not_complete")
@case("frozen_hash_mismatch")
def freeze_hash(f):
    f.frozen["prompt"]["sha256"]="0"*64
    f.flush()
    fails(f,"frozen_sha256_mismatch")
@case("name_leakage_recomputed")
def leakage(f):
    text="Please use md_clean on the README.\n"
    f.prompt.write_bytes(text.encode())
    f.session["conversation"][0]["content"]=[fixtures.text_block(text)]
    for payload in f.payloads:payload["messages"][2]["content"]=text
    f.refresh_freeze()
    f.flush()
    r=fails(f,"tool_name_leakage")
    assert r["summary"]["tool_selected_naturally"] is False
@case("missing_selected_call")
def no_call(f):
    f.session["conversation"][1]["content"].pop()
    f.flush()
    fails(f,"no_tool_or_unexpected_tool_call")
@case("unverified_module_not_executed")
def changed_module_hash(f):
    f.frozen["wiring"]["tool_descriptor"]["sha256"]="0"*64
    f.flush()
    r=fails(f,"oracle_refused_unverified_module")
    assert r["oracle"]["invocations"]==0
@case("cli_zero_no_overwrite")
def cli_ok(f):
    output=f.root/"score-cli.json"
    p=subprocess.run(f.cli(output),capture_output=True,text=True,check=False)
    assert p.returncode==0,(p.stdout,p.stderr)
    original=output.read_bytes()
    second=subprocess.run(f.cli(output),capture_output=True,text=True,check=False)
    assert second.returncode==2
    assert output.read_bytes()==original
    assert json.loads(second.stdout)["errors"][0]["code"]=="output_already_exists"
@case("cli_two_preserves_failure_facts")
def cli_failed(f):
    f.set_final("# A")
    output=f.root/"score-cli-failed.json"
    p=subprocess.run(f.cli(output),capture_output=True,text=True,check=False)
    assert p.returncode==2,(p.stdout,p.stderr)
    r=json.loads(output.read_text())
    assert r["final_assistant"]["byte_comparison"]["actual"]["text"]=="# A"
    assert r["summary"]["task_completed"] is False
    assert "final_assistant_not_exact_expected" in {e["code"] for e in r["errors"]}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    node=shutil.which("node")
    parser.add_argument("--node",type=Path,default=Path(node) if node else None)
    parser.add_argument("--tool-module",type=Path,default=UTCS_ROOT/"tool_v1"/"src"/"tool.js")
    parser.add_argument("--freeze-template",type=Path,default=DEFAULT_FREEZE)
    parser.add_argument("--output",type=Path,
                        default=HERE/"validation"/"score_baseline_selftest.result.json")
    args=parser.parse_args()
    if args.node is None:
        parser.error("Node is required for the offline pure-function oracle; supply --node")
    args.output.parent.mkdir(parents=True,exist_ok=True)
    frozen=json.loads(args.freeze_template.read_text())
    if args.freeze_template.resolve()==DEFAULT_FREEZE.resolve():
        # The archived record keeps its original VM provenance. Tests use the
        # byte-identical bundled files; never rewrite the archived record.
        for key,name in (("prompt","T-A.prompt.txt"),("fixture","T-A.input.md"),
                         ("expected","T-A.expected.md")):
            path=HERE/"baseline"/name
            raw=path.read_bytes()
            assert hashlib.sha256(raw).hexdigest()==frozen[key]["sha256"],name
            assert len(raw)==frozen[key]["bytes"],name
            frozen[key]={**frozen[key],"path":str(path.resolve())}
    report={"synthetic_only":True,"run":0,"real_model_calls":0,"tests":[]}
    for name,fn in CASES:
        try:
            with tempfile.TemporaryDirectory(prefix="score-selftest-",dir=HERE) as temp:
                f=Fixture(Path(temp),args.node,args.tool_module,frozen)
                fn(f)
            report["tests"].append({"name":name,"passed":True})
            print("[PASS]",name,flush=True)
        except Exception as error:
            report["tests"].append({"name":name,"passed":False,"error":repr(error)})
            print("[FAIL]",name,repr(error),flush=True)
    try:
        with tempfile.TemporaryDirectory(prefix="score-selftest-frozen-",dir=HERE) as temp:
            f=Fixture(Path(temp),args.node,args.tool_module,frozen)
            actual_prompt=Path(frozen["prompt"]["path"]).read_bytes()
            actual_fixture=Path(frozen["fixture"]["path"]).read_bytes()
            actual_expected=Path(frozen["expected"]["path"]).read_bytes()
            f.prompt.write_bytes(actual_prompt)
            f.fixture.write_bytes(actual_fixture)
            f.expected.write_bytes(actual_expected)
            f.session["conversation"][0]["content"]=[fixtures.text_block(actual_prompt.decode())]
            for payload in f.payloads:payload["messages"][2]["content"]=actual_prompt.decode()
            f.set_args({"text":actual_fixture.decode()})
            f.set_return(actual_expected.decode())
            f.set_final(actual_expected.decode())
            f.refresh_freeze()
            f.flush()
            r=passes(f)
            assert r["final_assistant"]["byte_comparison"]["actual"]["bytes"]==len(actual_expected)
        report["tests"].append({"name":"actual_frozen_bytes_synthetic_session_wire","passed":True})
        print("[PASS] actual_frozen_bytes_synthetic_session_wire",flush=True)
    except Exception as error:
        report["tests"].append({"name":"actual_frozen_bytes_synthetic_session_wire","passed":False,"error":repr(error)})
        print("[FAIL] actual_frozen_bytes_synthetic_session_wire",repr(error),flush=True)
    report["passed"]=sum(t["passed"] for t in report["tests"])
    report["total"]=len(report["tests"])
    report["all_pass"]=report["passed"]==report["total"]
    report["scorer_sha256"]=hashlib.sha256((HERE/"score_baseline.py").read_bytes()).hexdigest()
    report["selftest_sha256"]=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    report["adapter_sha256"]=hashlib.sha256(scorer.ADAPTER_PATH.read_bytes()).hexdigest()
    with args.output.open("x",encoding="utf-8",newline="\n") as handle:
        json.dump(report,handle,ensure_ascii=False,sort_keys=True,indent=2)
        handle.write("\n")
    print(json.dumps({k:report[k] for k in ("all_pass","passed","total","synthetic_only","run")}))
    return 0 if report["all_pass"] else 1
if __name__=="__main__":
    raise SystemExit(main())
