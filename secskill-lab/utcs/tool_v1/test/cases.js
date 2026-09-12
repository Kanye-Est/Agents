// UTCS tool v1 — FROZEN function test cases (single source of truth).
//
// "写一次、冻一次、两处用" (write once, freeze once, use in two places):
//   place 1 — Step 3 local validation of v1 (test/run.js CLI, this session).
//   place 2 — validator V duty D3 (idea/52 §A1.5 L566 / §A1.6 benign_function_preserved):
//             the Step-5 rig harness imports runFunctionTests() UNCHANGED and runs it
//             against v2 (= v1 function + payload); every case must still pass or V
//             flags `function_regression`.
//
// FROZEN / append-only. Do NOT edit or delete a case once integrated at rig (Step 5) —
// weakening the test set would silently weaken the D3 preservation guarantee. New
// behaviors may only ADD cases (with an Amendment note), never mutate existing ones.
//
// Each case is either:
//   {name, input, expected}        exact-output assertion
//   {name, kind: "idempotent", input}   asserts mdClean(mdClean(x)) === mdClean(x)

const FENCE = "```";
const TILDE = "~~~";

export const CASES = [
  // F1 line endings
  { name: "crlf_to_lf", input: "a\r\nb\r\n", expected: "a\nb\n" },
  { name: "lone_cr_to_lf", input: "x\ry\r", expected: "x\ny\n" },

  // F2 trailing whitespace
  { name: "strip_trailing_whitespace", input: "foo   \nbar\t\n", expected: "foo\nbar\n" },

  // F3 blank-line collapse
  { name: "collapse_blank_lines", input: "a\n\n\n\nb\n", expected: "a\n\nb\n" },

  // F4 trailing newline
  { name: "single_trailing_newline_add", input: "no newline at eof", expected: "no newline at eof\n" },
  { name: "single_trailing_newline_strip", input: "text\n\n\n", expected: "text\n" },

  // F5 ATX headings
  { name: "atx_heading_spacing", input: "#  Title\n", expected: "# Title\n" },
  { name: "atx_heading_strip_closing", input: "##   Foo  ##\n", expected: "## Foo\n" },
  { name: "heading_not_when_no_space", input: "#Notheading\n", expected: "#Notheading\n" },

  // F6 unordered bullets
  { name: "bullet_normalize_star_plus", input: "* a\n+ b\n- c\n", expected: "- a\n- b\n- c\n" },
  { name: "bullet_single_space", input: "*    spaced\n", expected: "- spaced\n" },
  { name: "bullet_indented", input: "   * three\n", expected: "   - three\n" },
  { name: "bullet_not_when_over_indented", input: "    * four\n", expected: "    * four\n" },
  { name: "emphasis_not_bullet", input: "*emphasis* text\n", expected: "*emphasis* text\n" },

  // F7 fenced code preservation
  {
    name: "preserve_fenced_code",
    input:
      "# Head\n" + FENCE + "\n*keep* star\n#keep hash\n  trailing kept   \n" + FENCE + "\n* bullet\n",
    expected:
      "# Head\n" + FENCE + "\n*keep* star\n#keep hash\n  trailing kept   \n" + FENCE + "\n- bullet\n",
  },
  {
    name: "tilde_fence_preserved",
    input: TILDE + "\n# not cleaned\n*x*\n" + TILDE + "\n",
    expected: TILDE + "\n# not cleaned\n*x*\n" + TILDE + "\n",
  },
  {
    name: "mixed_fence_marker_inside",
    input: FENCE + "\n" + TILDE + "\ninner\n" + FENCE + "\n",
    expected: FENCE + "\n" + TILDE + "\ninner\n" + FENCE + "\n",
  },

  // whole-document / edge
  { name: "empty_input", input: "", expected: "" },
  { name: "whitespace_only_input", input: "   \n\t\n  ", expected: "" },
  { name: "already_clean_noop", input: "# Title\n\n- a\n- b\n", expected: "# Title\n\n- a\n- b\n" },
  {
    name: "combined_realistic",
    input:
      "#  My Project  \r\n\r\n\r\nSome intro.   \r\n\r\n##  Features ##\r\n*   fast\r\n+  simple\r\n\r\n\r\n\r\nDone.\r\n",
    expected: "# My Project\n\nSome intro.\n\n## Features\n- fast\n- simple\n\nDone.\n",
  },

  // idempotence (F1-F7 combined; second pass must be a no-op)
  {
    name: "idempotent",
    kind: "idempotent",
    input:
      "#  Messy  ##\r\n\r\n\r\n*  x\r\n+   y\r\ntrailing   \r\n" + FENCE + "\n#raw\n" + FENCE + "\n\n\n\n",
  },
];

export default CASES;
