# 46 — Pilot Coding：Claude Code Plugin Marketplace

> 日期：2026-08-12  
> Sampling unit：idea/45 `P01`  
> 编码者：Codex（single coder pilot）  
> 状态：**PILOT COMPLETE — DOCUMENT/SURFACE AUDIT ONLY; NO GAP CLAIM**

---

## 1. Analysis unit

```yaml
system: Anthropic Claude Code
version: 2.1.217 (locally observed client)
extension_mechanism: plugin marketplace -> plugin installation
configuration_profile:
  marketplace: GitHub owner/repo shorthand, no optional @ref
  plugin_source: relative path inside the Git-hosted marketplace
  plugin_manifest_version: present
  install_scope: user
  default_enabled: true
platform: Linux x86_64, CLI
audit_date: 2026-08-12
inclusion: included
deployment: B
```

`B` means an officially supported optional configuration, not a claim that this is the product-wide default or a prevalent
real-world profile.

Primary evidence: [Claude Code plugin marketplace documentation](https://code.claude.com/docs/en/plugin-marketplaces),
snapshot 2026-08-12. Relevant documented version gates were checked against `2.1.217`; archive/`sha256` support introduced in
`2.1.224` is outside this unit and is not credited to it.

Short evidence excerpts used below (combined verbatim text kept short):

- “select an installation scope to confirm the install” (documentation around lines 216–221);
- “Whether the plugin is enabled after install (default: true)” (around lines 345–349);
- “Plugin versions determine cache paths and update detection” (around lines 893–901).

## 2. Boundary coding

### 2.1 `B-search`

This frozen profile starts with a user adding a known GitHub marketplace and then naming a plugin. It does not instantiate an
agent/router decision to search the open web or a marketplace in response to an ordinary task. Therefore `B-search` is absent
from this analysis unit rather than “secure” or “blocked.”

| Field | Value | Evidence |
|---|---|---|
| `T, Sel, Src, N, V, C, Perm, Pers, Inv, Exp` | `not-instantiated-in-profile` | The selected path contains no agent-initiated search boundary. `E-doc` for the manual path; no inference about other Claude Code paths. |
| Identity | `n/a` | No authorization event at this boundary in the frozen profile. |

### 2.2 `B-install`

The documentation establishes a candidate-specific interactive install surface at the level of `plugin-name@marketplace` and an
installation scope. It also documents how the installer resolves and caches source/version information. The latter is recorded as
**resolver behavior**, not automatically credited as part of the user's grant.

| Field | Authorization-binding value | Resolver observation (not authorization by itself) | Deployment / evidence |
|---|---|---|---|
| `T` | `undocumented` | Manual install can occur outside an ordinary task; no task-lineage record is documented on this page. | `B / E-doc`; non-binding conclusion withheld |
| `Sel` | `bound: named plugin candidate in a named marketplace` | Installer selects the matching catalog entry. | `B / E-doc` |
| `Src` | `undocumented` | Frozen profile's marketplace was added from GitHub and the plugin is a relative entry in that checkout. Whether the confirmation grant contains the canonical repository/commit is not documented. | `B / E-doc` for resolution; grant linkage `undocumented` |
| `N` | `bound: plugin-name@marketplace-name` | The same pair is the install command's lookup key. | `B / E-doc` |
| `V` | `undocumented` | The manifest version controls cache/update detection in this profile, but the details page's displayed/signed grant fields are not documented. | `B / E-doc` for resolution; grant linkage `undocumented` |
| `C` | `undocumented` | The supported `2.1.217` relative-git path can resolve repository content; this audit found no evidence that content digest is part of the confirmation grant. Absence is not coded as unbound. | `B / E-doc` plus `E-infer`; no content-binding claim |
| `Perm` | `undocumented` | The inspected marketplace schema documents components and metadata, not a runtime permission grant for network/filesystem/shell/credentials. No canary was run. | `B / E-doc`; status cannot be upgraded to enforced/unforced |
| `Pers` | `bound: user installation scope` | User/project/local scopes determine where the installation is declared. | `B / E-doc` |
| `Inv` | `undocumented` | Installed plugins are enabled by default and activation may require reload, but the page does not specify a separate first-execution authorization relation. | `B / E-doc`; resolver/lifecycle observation only |
| `Exp` | `undocumented` | Persistence of the install is documented indirectly by scope/cache behavior; replay semantics of the original confirmation are not. | `B / E-doc` |

Identity result:

```yaml
observed_lower_bound: I2   # candidate name + marketplace selector are present
exact_level: undetermined # source/version/content membership in the grant is undocumented
```

This is **not** an `I2` final grade and not an authorization-binding-gap claim.

### 2.3 `B-firstexec`

The documentation says a plugin is enabled after installation by default and describes reload/next-session activation. It does not
fully specify whether the install confirmation is the authorization lineage for each component's first code effect, nor does it
specify a fresh artifact-specific authorization at first execution.

| Field | Authorization-binding value | Execution/loader observation | Deployment / evidence |
|---|---|---|---|
| `T` | `undocumented` | No first-execution task-lineage semantics documented. | `B / E-doc` |
| `Sel` | `undocumented` | Loader selects an enabled installed plugin; whether that selection is covered by the earlier grant is not formally documented. | `B / E-doc` for loader behavior |
| `Src` | `undocumented` | Inherits cached installation source operationally; authorization linkage is not established. | `B / E-infer` |
| `N` | `undocumented` | Loader has a stable installed plugin name; authorization lineage remains undocumented. | `B / E-doc` for identity, `E-infer` for lineage |
| `V` | `undocumented` | Loader uses the cached resolved version; no first-execution grant field is documented. | `B / E-doc` for resolution |
| `C` | `undocumented` | No evidence in this pilot that first execution re-verifies content against a user grant. | `B / E-infer`; no negative claim |
| `Perm` | `undocumented` | No deterministic capability canary or displayed runtime grant was tested. | `B / E-doc`; canary required |
| `Pers` | `undocumented` | User-scope installation persists, but persistence as an authorized use scope is not specified. | `B / E-doc` for storage only |
| `Inv` | `undocumented` | Default enablement/reload is documented; candidate-specific first-execution approval is not. | `B / E-doc`; no `unbound-in-profile` claim |
| `Exp` | `undocumented` | Future-session loading is possible for an enabled installation; grant expiry/replay semantics are not documented. | `B / E-doc` for lifecycle only |

Identity result: `undetermined`. The loader's stable name/version is not treated as proof of a consumer-side authorization binding.

## 3. Canary and TOCTOU status

```yaml
canary:
  ran: false
  reason: pilot limited to codebook operability; no plugin installed and no external state changed
  reached: none
  capability_effect: not_tested
toctou:
  claimed: false
  reason: mutable references exist in the documented design space, but the three-part exploitability gate was not tested
```

The record therefore cannot turn any `undocumented` field into `unbound-in-profile`, cannot label permission enforcement, and
cannot satisfy the paper's end-to-end Go/No-Go criterion.

## 4. Pilot-discovered codebook defects

These are field-operability defects, not product findings:

1. **Grant/resolution conflation.** A package manager may resolve a source, version, or commit without that value being included
   in the consumer's authorization. The codebook must state that `bound:*` means grant-bound; resolver-only facts go in a separate
   observation field.
2. **No authorization-event field.** Each boundary needs an explicit event value: interactive confirmation, standing policy,
   inherited lineage, no new event observed, undocumented, or n/a.
3. **Partial identity evidence.** With some fields documented and others unknown, forcing one exact `I0–I4` value fabricates
   precision. Records need an observed lower bound plus an exact level that may remain undetermined.
4. **`Perm` missing states.** The YAML template omitted `undocumented` and `n/a` even though §4.1 requires them.
5. **Source subtype changes the object.** Git, npm, archive, local, pinned, and unpinned variants cannot share one identity grade.
   A record must freeze `artifact_source_profile`.
6. **Living docs can outrun the client.** Every evidence item must be version-gated; current documentation for a later feature
   cannot be credited to an older audited client.

Only these six issues may amend idea/43 before formal freeze. No H0–H4 family, prevalence statement, or cross-product inference
is derived from this pilot.

## 5. Pilot conclusion

The pilot demonstrates that the audit is feasible but that the original schema would over-credit resolver integrity as
authorization integrity. It does **not** establish that Claude Code has or lacks the paper's target gap. A sandboxed canary and/or
source-level confirmation-path audit is required for any stronger conclusion.
