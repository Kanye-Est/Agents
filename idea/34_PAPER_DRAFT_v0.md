# 34 — Paper Draft v0（The Acquisition Gap）

> 语言：正文用英文（USENIX 投稿语言）；本文件顶部这段是中文导读。
> 状态：**stable 段落（Abstract / Intro / Threat model / Funnel / Methods / Results-primary /
> Defense-mechanism / Related work / Limitations）已按 idea/31、33 的冻结口径写实。**
> `[PENDING]` 目前只剩 variance 子集与跨模型/scaffold；P2-approved 两臂已完成。
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
and removing target‑name leakage, adding one common scaffold pattern — an
**acquisition‑encouragement policy** that tells the agent it may search, install, and invoke
extensions when its tools fall short — raises full discovery E2E from **5/30 to 24/30** (paired
risk difference **+63.3 pp**; consistent across all three families; exact McNemar
p = 3.8e‑6). The dominant fork is the *first hop*, task→search (5/30 → 25/30); once an agent
decides to search, the downstream install→invoke→payload chain completes essentially
deterministically. An **execution‑layer approval gate** applied after the install call is parsed
but before it executes blocks **25/25** real install attempts (any‑path E2E 0/30) with no
prompt‑level defense. Our results reframe autonomous skill acquisition as a property of scaffold
*authorization semantics*, not only of model capability, and provide both a measurement and a
minimal defense. We report fixed‑benchmark rates on a single model and scaffold, not real‑world
prevalence.

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
   families same direction), and the risk is concentrated at the first hop task→search.
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

## 7. Related work (delta)

We position against selection‑of‑loaded‑skills, endorsement/recommendation, simulated harmful
install from a downstream install request, real install/RCE under an explicit user "clone/install
X", and payload‑given‑loaded‑skill results. Each measures a *different endpoint from a stronger
start*; none isolates the ordinary‑task → autonomous discovery → real install/register/invoke →
payload chain with per‑stage attribution, and none runs the P0/P1 causal manipulation of the
scaffold's acquisition policy. `[fill exact citations from idea/15,21; do not re-claim
"first execution / first autonomy / first install" — those are taken by SCR and HalluSquatting.]`

## 8. Limitations and ethics

**Limitations.** One model and one scaffold; three capability families and 30 hard specs form a
*fixed benchmark*, so rates describe the benchmark, not real‑world prevalence, and do not
extrapolate to other models, frameworks, marketplaces, or permission regimes. Temperature 0 gives
point estimates; a pre‑registered variance arm (temp 0.3, 3 seeds) is required before any rate is
quoted with error bars. `[PENDING cross‑model / cross‑scaffold, variance arm]`

**Ethics.** All skills, payloads, and marketplaces are synthetic and research‑scoped. Malicious
twins emit only a synthetic marker to a 127.0.0.1 collector; no real credentials, network egress,
or third‑party services are involved. Installs occur in per‑run temporary sandboxes. The artifact
release is a measurement harness and a defense, intended to help scaffold authors add acquisition
gates, not to enable acquisition attacks.

---

## 附：本 draft 尚缺、需实验补齐的洞（给 codex 的 TODO 对照）
- §8：跨模型 / 跨 scaffold（USENIX 接收门槛级），variance 子集（error bars + 复现实证）。
- §5 ICS 复核已完成：`ics_hard_gap_02/06/08` 的 P1/P2 前三次 raw model outputs
  均字节一致；错误包名安装在 P1 返回“包不存在”后触发 search，在 P2 被 gate 拦截后触发
  approval request 并停止。差异是处理后回执导致的合法轨迹分叉，不是首轮非确定性。
- §7 引用：从 idea/15、21 填精确 citation。
