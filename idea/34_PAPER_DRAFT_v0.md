# 34 — Paper Draft v0（The Acquisition Gap）

> 语言：正文用英文（USENIX 投稿语言）；本文件顶部这段是中文导读。
> 状态：**全文 prose 已写实，并已并入三-cell generalization（Abstract/§1/§5/§7/§9/§10 按 idea/40+41 改完）。**
> 三 cell：Qwen×text（anchor 5→24，过门）、Llama×text（4→9，QR 反向未过门；但 install/payload 8→28 强复现）、
> Qwen×native-FC（4→12，ICS 反向未过门；install/payload 4→12，parse-fail 0）。定稿口径：attack 跨 cell 复现、
> functional primary 模型依赖、acquisition propensity scaffold 依赖、第一跳最稳、P2 处处 100% 拦截。
> `[PENDING]` 仅剩：variance 误差条 + M3 frontier cell + .bib + markdown→LaTeX（定稿后）。
> 数字全部对齐 `policy_hardgap_causal_v2_full_20260726.analysis.md` 与 idea/33，改结果前不要改这里的数。
> 口径红线沿用 idea/33 §7：只报 fixed-benchmark，不报现实 prevalence，不外推模型/框架。

---

## Title (primary + alternates)

- **The Acquisition Gap: How a Scaffold Policy Turns Ordinary Agent Tasks into Third‑Party Code Execution**
- *Advertising the Toolbox: Acquisition‑Encouragement as Implicit Install Authorization in LLM Agents*
- *From Capability Gap to Code Execution: A Same‑Trajectory Measurement of Task‑Induced Skill Acquisition*

## Abstract

LLM agents increasingly run on scaffolds that can extend themselves at run time: search a
skill/plugin marketplace, install a new skill, and invoke it. We ask whether an *ordinary
capability task* — one where the user never requests discovery or installation, and the needed
skill is not preinstalled — can by itself drive an agent through real discovery, on‑disk
installation, registration, invocation, and a malicious payload, and which part of the
*scaffold*, rather than the model, controls this. We introduce the **Acquisition Funnel**, a
same‑trajectory measurement that decomposes end‑to‑end risk into per‑stage conditional survival
and separates three mutually exclusive end states: **discovery E2E** (a genuine
search→retrieve→recommend→install→invoke→payload chain), **direct‑install E2E** (installing a
guessed package name without discovery), and **residual E2E**. On a controlled benchmark of 30
distinct hard‑artifact tasks across three capability families (PDF, iCalendar, QR), each backed
by a deterministic artifact verifier and a benign/malicious *skill twin* with identical
model‑visible metadata, we run a pre‑registered causal comparison on a fixed model
(Qwen3‑32B‑AWQ) and scaffold. Holding tool‑call format knowledge identical between conditions
and removing target‑name leakage, adding a self‑extension scaffold pattern — an
**acquisition‑encouragement policy** that tells the agent it may search, install, and invoke
extensions when its tools fall short — raises full discovery E2E from **5/30 to 24/30** (paired
risk difference **+63.3 pp**; consistent across all three families; exact McNemar
p = 3.8e‑6). The dominant fork is the *first hop*, task→search (5/30 → 25/30); once an agent
decides to search, the downstream install→invoke→payload chain completes essentially
deterministically. An **execution‑layer approval gate** applied after the install call is parsed
but before it executes blocks **25/25** real install attempts (any‑path E2E 0/30) with no
prompt‑level defense. Across a second model (Llama‑3.3‑70B) and a second, native function‑calling scaffold, the attack,
its first‑hop locus, and the gate defense replicate, while the *magnitude* is jointly modulated by
model competence and scaffold — a task‑success‑gated metric can even rank the model that executes
*more* payloads as the safer one. Our results reframe autonomous skill acquisition as a property of
scaffold *authorization semantics* as much as of model capability, and provide a measurement and a
minimal defense. We report fixed‑benchmark rates, not real‑world prevalence.

## 1. Introduction

Modern agent scaffolds (skill/plugin/MCP marketplaces, "install this tool" affordances) let an
agent acquire *new code* mid‑task. The security literature has separately studied selection of
already‑loaded skills, endorsement/recommendation of skills, install commands under an explicit
user request, and payloads that fire once a skill is loaded. What has not been isolated is the
**conjunction**: (a) a pure capability task with zero user intent to find or install anything;
(b) a target skill that is *not yet in the agent's hands*; (c) real external discovery →
on‑disk install → registration → invocation → payload; and (d) per‑stage attribution along a
single run.

We treat this as a measurement problem rather than a single attack demonstration, and we ask a
causal question about the *scaffold*: does a routine self‑extension policy — "if your tools are
insufficient, search the marketplace, install what you find, then call it" — function as an
*implicit authorization to install and execute third‑party code* on ordinary tasks?

**Contributions.**
1. **The Acquisition Funnel** (§3): a same‑trajectory decomposition of task‑induced acquisition
   into eight auditable stages, plus three mutually exclusive end states (discovery /
   direct‑install / residual E2E) that prevent "guessed‑name direct install" from being reported
   as a genuine discovery chain.
2. A **controlled, twin‑based benchmark** (§4): 30 distinct hard‑artifact tasks whose success is
   decided only by a deterministic file verifier (pypdf‑parsable PDF fields; standard
   VCALENDAR/VEVENT fields; OpenCV‑decodable QR payload), with benign/malicious twins that are
   byte‑identical in model‑visible metadata and differ only in a synthetic localhost marker.
3. A **pre‑registered causal result** (§5): under a clean single‑variable manipulation, an
   acquisition‑encouragement policy raises discovery E2E from 5/30 to 24/30 (+63.3 pp, all three
   families same direction), with the risk concentrated at the first hop task→search — and across a
   second model and a native function‑calling scaffold the attack and its first‑hop locus replicate
   while magnitude tracks model competence and scaffold.
4. An **execution‑layer approval gate** (§6): a scaffold‑side defense that intercepts the parsed
   install call before any install code runs, blocking 25/25 real attempts; with approval, benign
   twins recover 25/30 functional E2E with 0/30 payloads, while indistinguishable malicious twins
   retain the same utility path but fire 25/30 payloads, delineating gating from vetting.

## 2. Threat model and definitions

**Setting.** A benign user issues an ordinary capability task to an agent. The agent has a set of
built‑in tools and access to a skill marketplace via two meta‑tools (`search_skills`,
`install_skill`). The target skill is *not preinstalled*. Installation is a real filesystem
event (package copied into a per‑run sandbox, manifest hash verified, tool registered into the
agent's registry, then callable).

**Adversary.** A malicious skill author publishes a skill whose model‑visible card, name,
description, parameter schema, and normal output are identical to a benign twin; the malicious
version additionally exfiltrates a synthetic marker to a localhost collector on invocation. The
adversary does *not* control the user prompt and does *not* rely on the user asking to install
anything. (All payloads are synthetic and localhost‑only; §8.)

**Endpoints (per run, all auditable from structured events).**
- `search_called`, `target_retrieved`, `install_recommended`, `install_call_emitted`,
  `install_call_parsed`, `install_execution_started`, `installed_on_disk`, `manifest_verified`,
  `registered_in_agent`, `invoked`, `payload_fired`, `task_ok` (deterministic artifact verifier).
- `e2e = installed_on_disk ∧ manifest_verified ∧ registered ∧ invoked ∧ payload_fired ∧ task_ok`.
- `discovery_e2e = e2e ∧ search_called ∧ target_retrieved ∧ install_recommended`.
- `direct_install_e2e = e2e ∧ ¬search_called`. `residual_e2e = e2e ∧ ¬discovery ∧ ¬direct`.
- These three partition `e2e` exactly; **discovery E2E is our primary endpoint**.

## 3. The Acquisition Funnel

We write end‑to‑end risk as a product of conditional survival probabilities along one trajectory:

```
P(E2E) = P(gap) · P(retrieved|gap) · P(emitted|retrieved) · P(parsed|emitted)
       · P(executed|parsed) · P(on‑disk|executed) · P(invoked|installed)
       · P(payload ∧ task_ok | invoked)
```

Prior numbers in the literature report *different* endpoints of this product from *different*
starting points (selection given a loaded registry; endorsement at the answer layer; payload
given a loaded skill; E2E given an explicit user install request). They are not wrong, but they
cannot be extrapolated to ordinary‑task autonomous acquisition without measuring each stage from
the same neutral start. The funnel makes the *location of attrition* the object of study: a
policy can change risk by moving any single conditional, and our main empirical finding is that
one policy moves essentially only the first one.

## 4. Experimental design

**Model & scaffold.** Qwen3‑32B‑AWQ (fixed revision), vLLM, thinking mode off, served on
localhost; a repository‑local *audited* tool‑loop runner that records raw model turns, parser
outcomes, and execution start/end so that `emitted ≠ executed` is directly observable. Every
trial uses a fresh agent, history, tool registry, install root, artifact root, and collector.

**Capability families & tasks.** Three hard‑artifact families in which a text‑only reply cannot
pass: PDF (10 distinct `project/owner/due` specs), iCalendar (10 distinct `title/DTSTART/DTEND`),
QR (10 distinct exact payloads). Plus G0 (no‑gap single‑tool controls) and G1 (one soft‑gap
weekly‑brief prototype in wording variants, kept only for continuity and treated as secondary).
Prompts name the requested output format but never mention skills, search, installation, or
authorization.

**Twins & verifiers.** Each family has a benign and a malicious twin with identical model‑visible
metadata; success is decided only by an independent parser (pypdf strict; VCALENDAR field‑exact;
OpenCV QR decode to the exact payload). A pre‑registered failure audit classifies every
"installed+invoked but ¬task_ok" and every "searched/emitted‑install but never on disk" trial
into protocol vs behavioral causes.

**Policies (single‑variable manipulation).** `P0` (neutral affordance) and `P1`
(acquisition‑encouragement) share byte‑identical assistant preamble, the four tool‑call format
examples (with a placeholder install name, no real target name), and the policy tail; **P1 adds
exactly** the search→install→invoke recipe plus an advisory cue in the `search_skills`
description. `P2` is model‑visibly identical to P1 but an external approval bit is false, so a
parsed install is blocked before execution. The manipulation P0→P1 is therefore the full
*acquisition‑encouragement bundle*, not a single sentence.

**Pre‑registration & provenance.** One frozen primary (P0‑vs‑P1 discovery E2E, pooled over 30
hard specs, exact McNemar, directional), a frozen cross‑family robustness rule (pooled > 0; ≥2
families > 0; no family < 0; p<0.05 is *not* a decision threshold), manifest/source hashes, and a
pre‑results git commit. Main run: 3 policies × (G0+G1+PDF+ICS+QR)×10 = 150, malicious twin,
neutral framing, temperature 0.

## 5. Results

**Primary.** Adding the acquisition‑encouragement bundle raises hard discovery E2E from **5/30
(P0) to 24/30 (P1)**, paired risk difference **+63.3 pp**, with **19** discordant pairs favoring
P1 and **0** favoring P0 (exact McNemar p = 3.8e‑6). The frozen robustness rule is met: all three
families move the same way — PDF 1/10→8/10, ICS 0/10→6/10, QR 4/10→10/10 — with no negative
family. All P0 and P1 E2E successes are discovery E2E: `direct_install_e2e = residual_e2e = 0`,
so the effect is not guessed‑name direct installs or unrecorded retrieval paths.

**The bottleneck is the first hop.** `search_called` moves 5/30 → 25/30 (+66.7 pp); once P1
searches, all 25 trajectories retrieve the target, receive a recommendation, emit and parse the
correct install, land on disk, register, invoke, and fire the payload — 24 of 25 then pass the
artifact verifier. So the encouragement policy does not uniformly lift every conditional; it
almost entirely changes whether the agent *interprets the task as calling for external
capability*. Downstream acquisition, on this scaffold, is close to deterministic once initiated.

**Attack execution can decouple from task success.** In P1, the payload fired on **25/30** hard
tasks while **24/30** also produced the correct artifact. The single gap (P1‑PDF, `CEDAR-95`) is
a trial where the agent generated the correct PDF, then re‑invoked the skill with the install
receipt's placeholder (`project=...`) and overwrote the valid file — a *duplicate‑invocation*
orchestration failure, not an acquisition failure (10 P1 hard trials show duplicate invocations,
12 extra calls total). The security‑relevant quantity (real third‑party code execution) is
therefore ≥ the E2E quantity.

**Neutral affordance is not zero‑risk.** Even under P0, 5/30 tasks reach autonomous E2E,
concentrated in QR (4) and PDF (1), ICS (0) — enough to record that mere tool availability
carries residual risk, but not enough (and not cross‑family) to headline as general risk.

**Controls.** G0 is 10/10 `task_ok` under all three policies with zero search/install — the
encouragement does not damage baseline utility on tasks the built‑in tools already cover. G1 is
0/10 acquisition under P0/P1/P2 after target‑name leakage was removed (in the confounded v1 it
was 7/10; this v1→v2 drop is a contamination diagnosis, not a randomized effect).

**Generalization across models and scaffolds.** We ran the identical frozen design on a second
model (Llama-3.3-70B-Instruct-AWQ, text scaffold) and on a second tool-calling surface
(OpenAI-style native function calling on Qwen), each with its own passing tool-probe and
pre-registered provenance.

| Cell | discovery E2E P0→P1 | strict H_A | install+payload P0→P1 | once search → downstream |
|---|---|---|---|---|
| Qwen × text (anchor) | 5→24 (+63 pp, p=4e-6) | pass | 5→25 | install+payload 25/25; task 24/25 |
| Llama-70B × text | 4→9 (+17 pp, p=.27) | fail (QR 3→2) | 8→28 (+67 pp, p=2e-6) | install+payload 28/28; task 9/28 |
| Qwen × native FC | 4→12 (+27 pp, p=.02) | fail (ICS 1→0) | 4→12 | all through task 12/12 |

Three things replicate and two vary, and the split is the finding. *(i) The attack replicates:*
autonomous acquisition and real payload execution rise under P1 in every cell — strongest of all on
Llama (install+payload 8→28, 20 discordant pairs to 0, p=2e-6). *(ii) The first hop is the stable
bottleneck:* once the agent decides to search, the acquisition chain runs to payload in every cell
(Qwen-text 25/25, Llama 28/28, Qwen-native 12/12). *(iii) The defense replicates:* P2 blocks 100%
of installs before execution in all cells (25/25, 28/28, 12/12; payload 0). *What varies: (iv) the
functional primary is model-dependent.* The strict pre-registered cross-family criterion passes
only on the anchor; both other cells fail it by a single-count reversal in a *different* family
(Llama QR 3→2, Qwen-native ICS 1→0), and on Llama the functional effect is not even
pooled-significant. This is task competence, not safety: Llama acquires and runs the malicious skill
on 28/30 tasks but produces the correct user artifact on only 9 (the 19 misses are semantic
argument/spec errors, with zero parse failures). Strikingly, Llama fires *more* payloads than the
anchor (28 vs 25) while scoring *lower* functional E2E (9 vs 24) — a task-success-gated metric ranks
the more-exploited model as the safer one. *(v) Acquisition propensity is scaffold-dependent:*
moving Qwen from the text protocol to native function calling roughly halves how often it decides to
acquire (P1 search 24→12) with zero argument-parse failures — the effect is not a text-parser
artifact, but the scaffold modulates the first-hop decision. Net: the mechanism
(encouragement → acquire → execute), its first-hop locus, and the gate defense hold across our
cells; the *magnitude* is jointly governed by model competence (task success) and scaffold
(acquisition propensity).

## 6. Defense: an execution‑layer approval gate

**Denial (mechanism).** `P2` keeps the P1 model‑visible policy but denies the external approval
bit, intercepting each install *after parse, before execution*. Across hard tasks the agent still
emitted **25** install attempts (22 correct‑target after search; 3 ICS wrong‑name guesses), and
**25/25** were recorded `approval_gate_blocked` with `install_execution_started = 0`,
`installed_on_disk = 0`, any‑path E2E **0/30** (P1→P2 e2e 24→0, p = 1.2e‑7). The gate converts a
silent auto‑install into an explicit decision point.

**Authorized benign install (utility recovery).** With the approval bit set and the *benign* twin,
the gate no longer blocks: the acquisition path returns to exactly the P1 level
(search/install/invoke **25/30**) and task utility recovers to **25/30** `functional_e2e`
(PDF 9/10, ICS 6/10, QR 10/10) with `payload_fired` **0/30**. (P1's 24/30 utility on the malicious
run was one PDF lost to a duplicate‑invocation overwrite, not to the gate.) So the gate is not a
blanket block: authorized, known-benign skills complete the task with no residual attack.

**Authorized malicious install (boundary).** With approval set and the *malicious* twin, the
observable acquisition and utility path is identical to the benign arm: search, install, invoke,
`task_ok`, and `functional_e2e` are all **25/30** (PDF 9/10, ICS 6/10, QR 10/10), and no call is
blocked. The sole systematic change is `payload_fired`, from **0/30** for benign twins to
**25/30** for malicious twins (25 benign=0/malicious=1 discordant pairs, 0 reverse;
exact McNemar p = 5.96e‑8). Thus the gate governs *whether* an install is authorized, not
*whether the authorized skill is safe*.

**What the gate does and does not do.** The gate's contribution is to remove *silent, autonomous*
installation — acquisition becomes an explicit, logged, authorizable event, i.e., a policy‑
enforcement and audit point. Its limit follows directly from our threat model: the benign and
malicious twins are *indistinguishable in every model‑visible field*, so a human (or policy)
approver at the gate sees exactly what the agent saw and has no additional information to decide
with. We verified this equality for all 30 paired tasks: policy-prompt and task-spec hashes match,
the three benign/malicious `SKILL.md` pairs are byte-identical, and every pair has the same
`visible_market_sha256`; only the hidden package implementation differs. The gate therefore does
not solve skill *vetting*; it *shifts* risk from autonomous
acquisition to an under‑informed approval, and must be paired with skill provenance,
static/reputational vetting, or capability scoping to be sufficient. We frame this as the correct
division of labor — the gate is the necessary control point, provenance is the necessary
information — and as motivation for provenance‑aware acquisition policies rather than as a complete
defense.

## 7. Discussion and implications

**Acquisition risk is a scaffold-policy property, not only a model property.** Under an identical
model and identical tool-call knowledge, moving one benign-intended scaffold policy — "if your
tools fall short, search, install, and call an extension" — moved full discovery E2E from 5/30 to
24/30. The policy names no skill and tells the agent to do nothing unsafe, yet it functions as an
*implicit authorization*: it converts ordinary tasks into real third-party code acquisition and
execution. Scaffold and platform designers thus own a choice that is easy to treat as a usability
default (advertising self-extension) but that carries an authorization semantics (granting install
authority on the model's judgment).

**Model and scaffold set the magnitude, not the mechanism.** The cross-cell data (§5) sharpens
this: the acquisition mechanism and its first-hop locus hold for a second model and a native
function-calling scaffold, but two different knobs set how bad it gets. Scaffold governs
*propensity* — native function calling halved Qwen's acquisition rate with unchanged mechanics — so
the same encouragement is more or less dangerous depending on how a platform surfaces its tools.
Model competence governs *whether the user is also served* — Llama executed the payload more often
than the anchor yet completed fewer tasks — so a defender who scores only task-gated E2E will
systematically under-rank the least capable, and here most-exploited, models. Both point the same
way: acquisition risk cannot be read off a single ASR number or a single setting.

**The leverage point is the first hop.** Attrition concentrated almost entirely at task→search
(P0 5, P1 25 of 30); once an agent decided to acquire, retrieval, installation, registration,
invocation, and payload survived essentially without loss. Two implications follow. First,
defenses that act at invocation time — scanning a skill's behavior after it loads — are
structurally late: on this scaffold the malicious code has already been fetched, installed, and run
by then; the defensible boundary is the acquisition *decision*, before search or before execution.
Second, an ASR reported from a strong start (a loaded skill, or an explicit install request) can
badly misestimate ordinary-task risk in either direction, because it prices only the
near-deterministic tail and omits the one conditional that actually varies.

**Gating is necessary but not sufficient; provenance is the missing primitive.** The
execution-layer gate blocks every unauthorized install and, once a benign skill is authorized,
restores task utility with no payload — a clean split between *whether to install* and *what the
task needs*. But the boundary arm shows the ceiling: with benign and malicious twins identical in
every model-visible field (equal `SKILL.md` bytes and market hashes across all 30 pairs), an
authorized malicious install still fires 25/30 payloads. An approver at the gate has exactly the
information the agent had — none that separates the twins — so the gate *relocates* the trust
decision rather than resolving it, shifting the attack from autonomous acquisition to
social-engineering an under-informed approval. Making the gate sufficient needs information the
metadata does not carry: signed publisher provenance, install-time static/behavioral analysis,
task-scoped capability manifests, or reputation. We therefore recommend that scaffolds treat
acquisition as an explicit, logged event gated on *provenance*, not merely on user assent.

**A reusable measurement standard.** Independent of this attack, the funnel and its three mutually
exclusive endpoints (discovery / direct-install / residual E2E) let one report acquisition risk
without conflating "guessed a package name" with "discovered and installed one," and localize where
a policy or model changes risk. We offer per-stage conditional survival, a deterministic task
verifier, benign/malicious twins with verified model-visible equivalence, and a pre-registered
primary as a template for evaluating self-extending agents; our own v1→v2 correction — a leaked
target name and paraphrase-only tasks inflating an early signal — is a concrete example of why
per-stage, pre-registered measurement matters.

## 8. Related work

**Post‑load skill attacks.** A large body of work measures what a malicious skill can do *once it
is already loaded into the agent's context*. Skill‑Inject (arXiv:2602.20156) reports up to ~80%
attack success from instructions hidden in skill files; Poise (arXiv:2606.07943) reaches ~89% with
a single setup line plus a side script while the user task still passes its verifier; MCPTox
(arXiv:2508.14925) poisons real MCP tool descriptions; and skill‑backdoor work (SkillTrojan,
arXiv:2604.06811; BadSkill, arXiv:2604.09378) pushes post‑load ASR to 97–99%. These define the
*severity* of the final stage but presuppose discovery, install, and registration; our funnel
begins before a skill is in the agent's hands and treats the loaded‑payload stage as one
conditional among several.

**Skill retrieval and selection in a registry.** Closest on the *pre‑load* side, Under the Hood of
SKILL.md (arXiv:2605.11418) shows a short trigger in SKILL.md manipulates registry discovery
(~86% pairwise win) and that a one‑sentence description change wins selection ~77.6% of the time
across models — but it explicitly does not report a separate metric for the agent *issuing an
install*. ToolHijacker (arXiv:2504.19793) frames tool use as retrieval+selection and drives
document‑optimized hijacking to high ASR on tools *already in the library*; ToolTweak
(arXiv:2510.02554) lifts selection among *interchangeable* tools from ~20% to ~81%. These measure
selection given retrieval, not autonomous on‑disk installation of a not‑yet‑present skill.

**Endorsement, install commands, and hallucinated names — the acquisition‑adjacent neighbors.**
Several recent works touch installation but from a stronger start or stop earlier on the chain.
SCR (arXiv:2606.15242) shows benign‑in‑isolation skills become harmful in composition; its neutral
CapFlow setting already uses non‑imperative task language, and its TrustLift setting raises harmful
installation to >83% — but from a *downstream install request* in a *simulated* market.
HalluSquatting (arXiv:2607.07433) measures real end‑to‑end install/RCE (40–100%) when the *user
explicitly asks to clone/install* a skill whose hallucinated name the attacker pre‑registered.
SearchGEO (arXiv:2606.16821) induces an agent to endorse a skill and emit an install *command*
(e.g., GPT‑5.4‑mini 17/18, Claude 0/18) but stops at command output; Skills That Don't Exist
(arXiv:2607.12340) measures recommendation hallucination (~36.9%) with an explicit‑authorization
install PoC; Neutral Prompting (arXiv:2605.29354) elicits a hallucinated package and a `pip
install` string (~63%) without executing it; and You Told Me To Do It (arXiv:2603.11862) shows
~85% compliance with adversarial README/setup instructions. Each reports a *different endpoint
from a different start* — recommendation, endorsement, install command, or install under explicit
user intent — and none measures the full ordinary‑task → autonomous discovery → real
install/register/invoke → payload trajectory with per‑stage attribution.

**Ecosystem, indirect injection, and in‑the‑wild evidence.** Indirect prompt injection (Greshake
et al., arXiv:2302.12173; InjecAgent, arXiv:2403.02691; AgentDojo, arXiv:2406.13352) establishes
that untrusted tool/document content can hijack agent actions, the mechanism behind our task→search
framing. Ecosystem measurements — "Do Not Mention This to the User" (arXiv:2602.06547; 98k skills,
157 confirmed malicious) and MCP security benchmarks (MSB, arXiv:2510.15994; MCPSecBench,
arXiv:2508.13220) — show malicious skills exist and spread in practice. Our contribution is
orthogonal: a same‑trajectory *measurement* of whether an ordinary task, absent any user install
intent, causes an agent to acquire and execute a not‑yet‑installed skill, plus a controlled
*causal* attribution of that behavior to a scaffold policy.

**Positioning.** We do not claim the first measurement of skill execution, of neutral/autonomous
triggering, or of installation — SCR (neutral triggering; simulated harmful install) and
HalluSquatting (real install/RCE under explicit user request) already occupy those. Our delta is
the *conjunction*: (a) a pure capability task, (b) a target not preinstalled, (c) real external
discovery→install→register→invoke→payload, (d) per‑stage attribution, and (e) a pre‑registered
P0/P1/P2 manipulation isolating the scaffold's acquisition policy. Table 1 places each neighbor by
where it stops on the funnel.

*[Bib note for codex: keys map to the arXiv IDs above; pull titles/authors from idea/15. Confirm
each ID and venue against the PDF before camera‑ready — several are 2026 preprints.]*

## 9. Limitations and ethics

**Limitations.** (1) *External validity.* We tested two models (Qwen3-32B-AWQ, Llama-3.3-70B-AWQ)
and two tool-calling scaffolds (text protocol, native function calling) — three cells beyond the
anchor. The attack, its first-hop locus, and the gate replicate across them, but the strict
pre-registered functional criterion passes only on the anchor and the magnitude is model- and
scaffold-dependent (§5). We have not yet tested a frontier/closed model, other marketplaces, or
other permission regimes, and we report fixed-benchmark rates, never population prevalence.
Crucially, the harness, the marketplace, the skill twins, and the P1 encouragement policy are
all researcher-constructed: the design establishes that *this* self-extension policy causally
produces autonomous acquisition and execution, not that production agent products commonly ship
such a policy or such a marketplace. The native function-calling arm varies the tool-calling
*surface* inside our harness, not a second real product framework. Anchoring the P1 policy and the
market to observed production scaffolds is required before any claim of real-world commonness.
(2) *Task breadth.* Thirty distinct specs span three capability families (PDF,
iCalendar, QR); a low rate in any one family (e.g., ICS) reflects that benchmark, not "hard gaps
are safe." (3) *Estimand.* P1−P0 measures the whole acquisition-encouragement bundle (a
system-prompt recipe plus an advisory tool description), not a single sentence, by design.
(4) *Determinism.* Temperature 0 gives point estimates; a pre-registered variance arm (temp 0.3,
three seeds) is required before any rate is quoted with error bars `[PENDING]`. (5) *Orchestration
confound.* One P1 task failed only because a duplicate invocation overwrote a correct artifact — an
agent-orchestration failure we report separately (attack execution, 25/30 payloads, is therefore ≥
the 24/30 E2E), not an acquisition failure.

**Ethics.** All skills, payloads, and marketplaces are synthetic and research-scoped. Malicious
twins emit only a synthetic marker to a 127.0.0.1 collector; there is no real credential access,
network egress, or third-party service, and installs occur in per-run temporary sandboxes on a
localhost-only model server. We release a measurement harness, a benchmark, and a defense to help
scaffold authors add provenance-aware acquisition gates; the artifact is not usable as an
acquisition attack against real marketplaces, and we will follow coordinated disclosure with
affected scaffold/marketplace maintainers before release.

## 10. Conclusion

Self-extending agents turn a capability gap into an acquisition action. On a fixed
Qwen3-32B × HelloAgents benchmark with a pre-registered causal design, a scaffold policy
that encourages self-extension raised full task-induced discovery E2E from 5/30 to 24/30, with the
risk concentrated at the task→search decision; an execution-layer approval gate blocked
unauthorized installs and restored utility for authorized benign skills but did not vet them.
Across a second model and a native function-calling scaffold, the attack, its first-hop locus, and
the gate replicate while magnitude tracks model competence and scaffold — a task-gated metric can
even rank the more-exploited model as safer. We release the Acquisition Funnel measurement and the
twin benchmark. The take-away for builders is narrow and actionable:
advertising self-extension is an authorization decision, the place to enforce it is the acquisition
boundary, and enforcement must be tied to skill provenance.

---

## 附：本 draft 尚缺、需实验补齐的洞（给 codex 的 TODO 对照）
- 跨模型/scaffold 三 cell 已并入 §5/§7/§9/§10/Abstract（idea/40、41）。剩：variance 误差条 + M3 frontier cell + .bib + markdown→LaTeX（定稿后）。
- §5 ICS 复核已完成：`ics_hard_gap_02/06/08` 的 P1/P2 前三次 raw model outputs
  均字节一致；错误包名安装在 P1 返回“包不存在”后触发 search，在 P2 被 gate 拦截后触发
  approval request 并停止。差异是处理后回执导致的合法轨迹分叉，不是首轮非确定性。
- §7 引用：已填精确 citation（arXiv IDs 见正文；.bib 的 titles/authors 从 idea/15 取，camera-ready 前逐条回 PDF 核对 ID/venue）。剩：Discussion/Implications 一节（provenance 缺口 + 对 scaffold 设计者的建议）待起草。
