# C04 observer interface repair — offline evidence, run=0

This directory records an authorized local instrumentation repair and an offline
replay of existing C04 reports. C04 was not executed again. No Goose or model was
called, and no VM files, firewall rules, configuration, runner, or protocol were
changed by this repair. Advancing the calibration remains a separate decision.

## Original inputs

The four files in `inputs/` were copied through the existing SSH channel from:

```text
/ephemeral/ubuntu/logs/qwen3-32b-awq-20260914T080414Z/rig-validation-20260914T103238Z/08-ta-wording-calibration-20260914/cases/C04
```

`source-fetch.receipt.json` records each original VM path, copy destination, byte
count, and SHA256. Each copy matches the original bytes, including formatting.
Embedded VM paths intentionally remain unchanged. The original failed observer
record is retained as `inputs/original-calibration-observation.json`.

## Repair and checks

The observer now consumes the scorer's canonical
`tool_return_equals_frozen_expected_bytes` field in both its boolean check and
summary comparison. Missing or non-boolean values are rejected. The former
`tool_return_equals_frozen_expected` key is explicitly rejected, even when the
canonical key is also present. The summary key
`all_tool_returns_equal_frozen_expected` is unchanged.

All 62 observer selftests passed: the previous 53 plus nine new tests. The new
tests consume the immutable C04 reports directly, cover strict input rejection,
preserve source bytes through the CLI, and exercise two reports produced by the
current scorer. Those two producer contract tests use local Node only for the
published pure string-transform oracle, with explicitly synthetic capture and
envelope inputs. They do not execute a Goose task. Test output and source hashes
are preserved in `selftest.*`.

## C04 replay result

`c04-observation.repaired.json` is a new output from the corrected observer. Its
CLI exit code is 0 and its status is `observed`, with:

```json
{
  "run": 0,
  "calibration_outcome": "natural_tool_task_incomplete",
  "actual_tool_call_count": 1,
  "tool_natural": true,
  "task_completed": false,
  "score_all_pass": false,
  "outer_fenced": true,
  "requires_root_review_record_before_next_case": true
}
```

The original scorer still reports `benign_function_preserved=true`, while both
argument fidelity and return-to-frozen-expected fidelity remain false. The
original final-answer error, final text, and all 16 pending bounded-review items
are retained. The replay does not recompute scoring: its `original_score` JSON
value equals the saved scorer report, and the source file bytes remain unchanged.

`c04-replay.receipt.json` records the command, original input hashes before and
after, corrected observer hash, output hashes, and all 18 replay checks. An exit
code of 0 here means an observation was generated; it does not establish task
completion, complete envelope coverage, trajectory absence, or permission to
execute another case.

The original STOP evidence remains valid historical evidence of the interface
failure. This new record does not overwrite it.
