// UTCS tool v1 — function-test runner (the "two places" contract).
//
// runFunctionTests(fn) is the SINGLE entrypoint used in both places:
//   place 1 — Step 3 local validation:  runFunctionTests(mdClean)  (this file's CLI)
//   place 2 — validator V duty D3:       the Step-5 rig imports THIS function unchanged
//             and calls runFunctionTests(v2mdClean); the returned array becomes the
//             effect-observation record's `function_tests` field, which
//             validator_v.check_function_preserved() consumes.
//
// Output shape is FROZEN to match validator_v.py D3 input exactly:
//   [{ name: string, passed: boolean }, ...]
// (GENERATION_SPEC §S.6 record contract: "function_tests": [{"name":..,"passed":..}])

import fs from "node:fs";
import { pathToFileURL } from "node:url";
import { mdClean } from "../src/mdclean.js";
import { CASES } from "./cases.js";

/**
 * Run the frozen function-test set against a mdClean implementation.
 * @param {(input: string, options?: object) => string} [fn] defaults to v1 mdClean;
 *        the rig passes v2's implementation here.
 * @returns {Array<{name: string, passed: boolean}>}
 */
export function runFunctionTests(fn = mdClean) {
  return CASES.map((c) => {
    let passed;
    try {
      if (c.kind === "idempotent") {
        const once = fn(c.input);
        passed = fn(once) === once;
      } else {
        passed = fn(c.input) === c.expected;
      }
    } catch {
      passed = false; // a throw is a failure, never a silent pass
    }
    return { name: c.name, passed };
  });
}

export default runFunctionTests;

// ---- CLI: node test/run.js [--json] [--emit <path>] ----
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const results = runFunctionTests();
  for (const r of results) console.log(`  [${r.passed ? "PASS" : "FAIL"}] ${r.name}`);
  const allPass = results.every((r) => r.passed);
  const passCount = results.filter((r) => r.passed).length;

  const payload = { function_tests: results };
  if (process.argv.includes("--json")) console.log(JSON.stringify(payload, null, 2));
  const emitIdx = process.argv.indexOf("--emit");
  if (emitIdx !== -1 && process.argv[emitIdx + 1]) {
    fs.writeFileSync(process.argv[emitIdx + 1], JSON.stringify(payload, null, 2));
    console.log(`emitted function_tests -> ${process.argv[emitIdx + 1]}`);
  }

  console.log(
    allPass
      ? `FUNCTION TESTS PASSED (${passCount}/${results.length})`
      : `FUNCTION TESTS FAILED (${passCount}/${results.length})`
  );
  process.exit(allPass ? 0 : 1);
}
