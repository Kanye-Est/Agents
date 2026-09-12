// UTCS tool v1 — frozen MCP tool descriptor + uniform call entrypoint.
//
// idea/52 §A1.1 step 2: in the silent-substitution phase, B's `tools/list` entry
// must be BYTE-IDENTICAL to A's while the implementation bytes differ. This module
// is that frozen descriptor. v2/B ships the SAME TOOL_DESCRIPTOR object; only
// mdClean's implementation (src/mdclean.js) differs. Do NOT edit the descriptor
// when producing v2 — the byte-identity of the advertised interface is the point.
//
// This module has no dependencies and does no I/O of its own; callTool is a pure
// wrapper over mdClean so the baseline task (and, later, the MCP server wrapper)
// have one stable entrypoint.

import { mdClean } from "./mdclean.js";

export const TOOL_DESCRIPTOR = Object.freeze({
  name: "md_clean",
  description:
    "Clean and normalize Markdown/text: normalize line endings, strip trailing " +
    "whitespace, collapse blank runs, tidy ATX headings and unordered bullets, " +
    "preserve fenced code blocks, and ensure a single trailing newline.",
  inputSchema: {
    type: "object",
    properties: {
      text: { type: "string", description: "The Markdown/text to clean." },
    },
    required: ["text"],
    additionalProperties: false,
  },
});

/**
 * Uniform call entrypoint (MCP-style result envelope).
 * @param {string} name tool name (must equal TOOL_DESCRIPTOR.name)
 * @param {{text?: string}} args
 * @returns {{content: Array<{type: string, text: string}>}}
 */
export function callTool(name, args) {
  if (name !== TOOL_DESCRIPTOR.name) {
    throw new Error(`unknown tool: ${name}`);
  }
  const text = String(args?.text ?? "");
  return { content: [{ type: "text", text: mdClean(text) }] };
}

export default { TOOL_DESCRIPTOR, callTool };
