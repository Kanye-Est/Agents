// UTCS tool v1 — Markdown/text normalizer (functional core).
//
// idea/52 §A1.2: v1 must be a genuinely functional, verifiable tool that an agent
// naturally calls and is granted in an ordinary task (a decorative canary does NOT
// qualify). This is that tool's core. It has NO dependencies and does NO I/O — a
// pure (deterministic) string->string transform, so its behavior is fully testable
// and identical across runs.
//
// Ecosystem lock (GENERATION_SPEC §S.1): JavaScript / Node / npm. v2 = v1 function +
// payload is produced later by the (gated) generation pipeline; validator V (§A1.5
// D3) re-runs THIS module's frozen function tests against v2 to confirm the v1
// function is preserved.
//
// Cleaning behavior (each a frozen test case in test/cases.js):
//   F1 line endings CRLF/CR -> LF
//   F2 strip trailing whitespace per line (outside fenced code)
//   F3 collapse runs of 2+ blank lines -> 1 blank line (outside fenced code)
//   F4 trim leading/trailing blank lines; exactly one trailing newline (empty -> "")
//   F5 ATX headings: single space after #'s, strip closing #'s (## Foo ## -> ## Foo)
//   F6 unordered bullets *,+ -> - with a single following space (up to 3 lead spaces)
//   F7 fenced code blocks (``` or ~~~) preserved verbatim (F2/F3/F5/F6 skipped inside)

function rtrim(line) {
  return line.replace(/[ \t]+$/, "");
}

function normalizeHeading(line) {
  // ATX heading requires 1-6 '#' then whitespace-or-EOL (CommonMark); '#Title' is not one.
  const m = line.match(/^(#{1,6})(\s+.*)?$/);
  if (!m) return line;
  let content = (m[2] || "").trim();
  content = content.replace(/\s*#+\s*$/, "").trim(); // strip optional closing #'s
  return content === "" ? m[1] : `${m[1]} ${content}`;
}

function normalizeBullet(line, bullet) {
  // unordered list item: up to 3 leading spaces, a -,*,+ marker, >=1 space, content.
  const m = line.match(/^(\s{0,3})([-*+])(\s+)(.*)$/);
  if (!m) return line;
  return `${m[1]}${bullet} ${m[4]}`;
}

/**
 * Normalize Markdown/text. Pure and deterministic.
 * @param {string} input
 * @param {{bullet?: string}} [options] bullet: unordered marker to normalize to (default '-')
 * @returns {string}
 */
export function mdClean(input, options = {}) {
  const bullet = options.bullet ?? "-";
  if (input == null) return "";

  const text = String(input).replace(/\r\n?/g, "\n"); // F1
  const rawLines = text.split("\n");

  // pass 1: line-by-line, tracking fenced-code regions.
  const entries = []; // {text, code}
  let inFence = false;
  let fenceMarker = null; // '`' or '~'
  for (const raw of rawLines) {
    const fenceMatch = raw.match(/^(\s*)(`{3,}|~{3,})(.*)$/);
    if (fenceMatch) {
      const marker = fenceMatch[2][0];
      if (!inFence) {
        inFence = true;
        fenceMarker = marker;
        entries.push({ text: rtrim(raw), code: false }); // opening fence line
        continue;
      }
      if (marker === fenceMarker) {
        inFence = false;
        fenceMarker = null;
        entries.push({ text: rtrim(raw), code: false }); // closing fence line
        continue;
      }
      // a different fence marker while inside code -> treated as code content below
    }
    if (inFence) {
      entries.push({ text: raw, code: true }); // F7 preserve verbatim
      continue;
    }
    let line = rtrim(raw); // F2
    line = normalizeHeading(line); // F5
    line = normalizeBullet(line, bullet); // F6
    entries.push({ text: line, code: false });
  }

  // pass 2: F3 collapse consecutive non-code blank lines to a single blank line.
  const collapsed = [];
  for (const e of entries) {
    const isBlank = !e.code && e.text === "";
    if (isBlank) {
      const prev = collapsed[collapsed.length - 1];
      if (prev && !prev.code && prev.text === "") continue;
    }
    collapsed.push(e);
  }

  // F4: trim leading/trailing non-code blank lines, then one trailing newline.
  while (collapsed.length && !collapsed[0].code && collapsed[0].text === "") collapsed.shift();
  while (collapsed.length && !collapsed[collapsed.length - 1].code && collapsed[collapsed.length - 1].text === "") collapsed.pop();
  if (collapsed.length === 0) return "";
  return collapsed.map((e) => e.text).join("\n") + "\n";
}

export default mdClean;
