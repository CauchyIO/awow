# Proposal — repo-canonical knowledge in anchored repos: verdict only

**Status:** Draft (2026-09-16) — decisions taken in the walkthrough of 2026-09-16 (§5); filed as CAU-1612.
**Remit (decision 0):** awow adds a *repo-canonical* verdict to the reference-before-capture seam, offers the `adopting-okf` skill at anchored-repo registration, and fills the anchor record's entrypoint. awow owns **no write path** into a repo's bundle. A developer adding an ADR to their repo's docs during an anchored-repo session is ordinary development, not awow machinery; awow's only guidance at that moment is a pointer to the adopt skill's *Verify* list so an existing bundle stays conformant.
**Inputs:** [`canonical-knowledge-source-routing-design.md`](canonical-knowledge-source-routing-design.md) (the accepted parent — this proposal extends §5.4 and keeps §2.2 and §8 intact), [`hub-and-spoke-design.md`](hub-and-spoke-design.md) §3, [`jit-context.md`](jit-context.md), the `adopting-okf` and `knowledge-source-routing` skills, `context/tooling/knowledge-sources.md`, and board items CAU-1280, CAU-1519, CAU-1515, CAU-1247.

---

## 1. Outcome

An engineer working in an anchored repo states or discovers something durable about *that* repo — how its retries are structured, why a service boundary sits where it does, the runbook for its one nightly job. Today awow either pushes that fact into the anchor's knowledge base, where it does not belong, or classifies it external-canonical and records a pointer to a bundle nothing ever registered. After this change every awow gate that would capture the fact recognises it as **repo-canonical**: it writes nothing into the anchor knowledge base, presents the repo's bundle as the canonical home by URI, and leaves the capture to the developer, who adds the concept to the repo's docs the way they add any other file. At registration the repo's existing documentation is offered up for OKF adoption, so the bundle exists and the anchor's record routes to it read-only, exactly as the parent design already specifies. Nothing new is copied, cloned, mirrored, or written across a repo boundary in either direction.

## 2. The gap, precisely

The read side is complete. `context/tooling/knowledge-sources.md` §Anchored-repo records lets the anchor's record for a repo carry `knowledge.format: okf` and `knowledge.entrypoint`; `knowledge-source-routing` follows that entrypoint read-only; `adopting-okf` turns an existing docs folder into a conformant v0.2 bundle.

Two things are missing, and neither is a write path:

- **The seam has no verdict for the repo you are standing in.** Parent §5.4 and the routing skill's *Capture* section classify a durable write as hub-canonical, external-canonical, or uncertain authority. Every capture path — `/kb-mine`, `/kb-synthesize`, `/update-context`, the promotion ritual — resolves `inbox` and `kb_root` through `{ANCHOR}/context/tooling/knowledge-base.md`, and `mining.md` §Routing fixes `suggested_target` to the anchor's five subfolders. A fact about the anchored repo therefore lands in the anchor KB unless something names the repo as canonical, and nothing does: `{PROJECT}` holds mission, board-scope, do-not-propose, and `proposals/`, and no record says where the repo keeps its knowledge.
- **Registration never produces an entrypoint.** `/setup-awow`'s anchored track step 5 drafts the anchor record as "routing profile plus `anchored:` block"; the `knowledge:` block is optional in the profile and nothing in steps 1–5 fills it. `SETUP.md`'s five-step description matches. So even a repo whose docs are already a bundle is registered as an opaque repository.

Two facts frame the fix:

- **The read-only rule is correctly scoped and is not touched.** `knowledge-source-routing` forbids write-back "while acting from the ANCHOR"; `adopting-okf` forbids adoption "when reached through ANCHOR canonical-source routing". Neither says anything about a developer editing their own repo, because that is not awow's business.
- **No test covers the anchored track.** `tests/setup-awow/` has fourteen scenarios, none anchored; the anchored shape is exercised only by `tests/hooks/test_session_start.py` (connector tiers) and `tests/harness/*/wiring.sh` (payload plus connector).

## 3. Approaches

**A. Convention only.** Document that an anchored repo's `docs/` folder is where repo knowledge goes, add nothing to awow. Cheapest, but the seam still cannot name the repo as canonical, the anchor record still has no entrypoint, and "convention" here means every session re-derives the answer — the drift the path-token discipline exists to prevent. Rejected.

**B. Verdict only (recommended).** The anchored repo declares one thing — where its bundle root is — via the connector it already commits. awow's existing pieces do the rest: `adopting-okf` produces the bundle from existing docs at registration, the connector and the anchor record carry the entrypoint, and the seam gains a fourth verdict, *repo-canonical*, whose disposition is always reference-only. No inbox, no drain, no write path, no new command. Capturing into the bundle is the developer's ordinary work in their own repo.

**B′. Verdict plus a gated awow write.** As B, but awow also writes the concept into the bundle through its approval gate and creates the bundle root on first need. Rejected: it makes awow the owner of a write path into a repository's documentation, and with it the owner of that bundle's conformance, folder layout, and defaults — machinery for what is plainly development. It also needs an "empty bundle root" that `jit-context.md` §The contract already ruled out (a stub is worse than absence).

**C. A per-repo knowledge base** with its own `kb_root`, inbox, mining scope, and drain. **Declined**, not parked — §4.8 records why. In one line: it would have awow synchronise and conform content in a repository it routes to, which the parent design excludes by name.

## 4. Design

### 4.1 Registration — adopt or nothing

The anchored track gains one optional, gated offer inside step 4 (the anchored-repo PR). After drafting the connector, board-scope, and mission, the wizard looks for documentation worth routing to — a `docs/` or `knowledge/` folder, an ADR directory, Markdown outside `context/` and `proposals/` — and makes the fill-on-first-need offer in the CAU-1333 style: *"This repo has N Markdown docs under `<folder>`. Adopt them as an OKF bundle so the anchor can route to them? [adopt / not now]"*. Yes invokes `adopting-okf` over that folder with the diff-before-landing rule the skill already has; the metadata and index diff rides in the same anchored-repo PR, and the connector gains the `knowledge:` key (§4.2). No is recorded once in `setup-progress.md` and never re-asked by the wizard.

When there is nothing to adopt, the wizard writes nothing and records that. awow never creates a bundle root later, at registration or at any capture moment. A repo that acquires documentation afterwards adopts it by invoking `adopting-okf` directly — ordinary development in that repo — and re-runs the anchored track, which is already the repair entry point, to add the key and fill the record.

Step 5 (the anchor PR) copies the entrypoint from the connector into the record's `knowledge:` block. CAU-1519's fix to step 5's wording lands alongside if it has not landed first.

### 4.2 Declaration — the connector

The connector is the declaration. The anchored repo's root `AGENTS.md` frontmatter gains one optional key beside `anchor:` and `project:`:

```yaml
---
awow: anchored
anchor: https://github.com/CauchyIO/linear
project: entra
knowledge: docs/index.md
---
```

`knowledge:` is a repo-relative path to the bundle root `index.md`, the file that carries `okf_version`. Absent means "no bundle declared". `hooks/session-start.py` already parses this block with `frontmatter_value`; it reads the new key and, when present, adds one clause to the connected-tier message so the reflex knows the bundle root without a second lookup.

The anchor record's `knowledge.entrypoint` is the read-side copy of the same value. The connector is authoritative for *where in this repo*; the record is the routing convenience. A mismatch is handled the way `design-system.md` treats its token cache — re-read the source, report the drift, do not trust the cache. This is the two-file split the anchored shape already uses for identity: what is committed to the repo is the truth, what the anchor holds is the register.

### 4.3 The repo-canonical verdict

Parent §5.4 is amended with a fourth verdict:

| Verdict | When | Disposition |
|---|---|---|
| anchor-canonical | Team-specific: convention, local decision, ownership, cross-repo synthesis | Write to the anchor location through the normal gate (unchanged) |
| **repo-canonical** | The session runs in an anchored repo (connector present) **and** the fact is about this repo's code, shape, or operation | **Reference only.** No anchor KB write. Present the canonical home — the bundle root by URI when `knowledge:` is set, the repo's `resource` when it is not — and leave the capture to the developer. |
| external-canonical | Canonical in another source, including *another* anchored repo | Reference only (unchanged) |
| uncertain authority | Competing candidates | Ask (unchanged) |

Repo-canonical differs from external-canonical in one respect only: the session is *in* the canonical repo, so the gate can say so plainly — *"this belongs in this repo's docs, not the anchor KB; bundle root `docs/index.md`"* — and can add the one line of guidance in §4.6. It does not offer to write, to create a root, or to choose a folder. When no `knowledge:` key is present the verdict still holds; the reference names the repo, the gate notes once that no bundle is declared, and stops.

The verdict lives in the three places the seam already lives, and nowhere else: one sentence in `using-awow` §Route canonical knowledge, a short *Repo-canonical* paragraph in `knowledge-source-routing` §Capture, and a row in `context/tooling/knowledge-sources.md` §Reference before capture. Every gate that presents a knowledge placement — `/process-workitem`, `/process-transcript`, `/solution-design-flow`, the promotion ritual, `/kb-synthesize`'s drain plan — inherits it through the reflex, per parent §5.3, and is not edited. In the drain, a repo-canonical candidate takes the external-canonical action: a one-line reference in the anchor with the repo's canonical URI, and a `_synthesis-log.md` line naming the verdict. Guidance (`kind: guidance`) is team data and stays anchor-only, untouched.

### 4.4 What the anchor record gains

Nothing new in shape. The `knowledge:` block already exists in the profile; step 5 fills it from the connector. The anchored-repo record remains "an ordinary routable read-only source" as `knowledge-sources.md` says. The catalog gains no scope flag, no per-repo path, no clone path.

### 4.5 Board linkage from anchored-repo stories

Output-discipline Rule 1 gives the story skeleton a `## Reference` block of `context/knowledge-base/...` paths. Those are anchor-relative and mean nothing for a concept in an anchored repo. A story raised from an anchored repo links a bundle concept by its canonical URI: the record's `resource` plus the repo path, rendered as the provider's default-branch blob URL so the board makes it clickable and the link survives a clone moving. Never a local path, never a branch name. One line added to the shipped `output-discipline.md` seed and to `workitem-write` §3's placement note. The KB link discipline is unchanged: the board links in, the bundle never links back to a story.

### 4.6 Conformance — at adoption, then a pointer

Conformance is established once, at adoption, by `adopting-okf`'s own *Verify* step: non-empty `type` on every concept, root index declares the version and nested indexes carry no frontmatter, every concept reachable from its nearest index, local links resolve, no body or pre-existing frontmatter value altered. After that the bundle is the repo's to keep conformant, like its tests or its lint. awow's single contribution is the one line the repo-canonical gate adds when a bundle is declared: *"adding a concept? keep it conformant — see the adopt skill's Verify list."* No validator ships; parent §9.1 declined deterministic tooling until real usage shows a recurring structural failure, and `CauchyIO/linear` already carries `tools/validate_okf.py` from CAU-1247 as prior art if that day comes.

### 4.7 Failure and degraded behaviour

- **Not an anchored repo:** nothing here applies; standalone and anchor behaviour is unchanged.
- **Connector without `knowledge:`:** the verdict still holds; the reference names the repo's `resource`; the gate notes once that no bundle is declared and does not offer to create one.
- **`knowledge:` names a missing file, or a file that is not a bundle root:** report it once and point at the anchored track's repair re-run; never reference a guessed path, never fall back to an anchor write.
- **Bundle at an unsupported OKF version** (the Cauchy anchor is v0.1; the skill is v0.2): read as ordinary Markdown per parent §7; wherever awow itself emits OKF — the adopt skill, the catalog record — it writes v0.2 fields and never rewrites `okf_version`; the mismatch is reported once.
- **`{ANCHOR}` unresolvable:** the reflex already stops loudly; the verdict needs the anchor to rule out anchor-canonical, so the stop stands.
- **Session acting from the anchor, routed into this repo:** read-only, exactly as today. The verdict keys on CWD being the anchored repo, never on a routed match.

### 4.8 Out of scope — and what is declined

- **Approach C, a per-repo inbox, mining scope, and drain: declined, not parked.** No trigger condition. awow's remit ends at recognising where knowledge is canonical and routing to it. A per-repo drain would have awow own the lifecycle of content inside a repository it routes to — staging it, judging it, promoting it, keeping it conformant — which is exactly the custody the parent design excludes: its MVP "does not host, index, embed, copy, mirror, clone, or synchronize external content", does not "make all external systems conform to OKF", and does not "edit or write back to any external canonical source" (parent §8; §2.2). A repo's docs are external content from awow's point of view even when the session is standing in that repo; the anchor is the one knowledge base awow runs a ritual for.
- **Approach B′, an awow-owned write path into the bundle,** declined for the same reason at smaller scale (§3).
- **Creating a bundle root at any moment other than adoption of existing docs.** Never; §4.1.
- **Shipping awow's default `context/knowledge-base/` skeleton as an OKF bundle.** A real gap — the shipped skeleton has no root index while Cauchy's anchor has been a bundle since CAU-1247 — but it touches the KB README's *frontmatter-light* rule (OKF requires `type` on every concept) and the drain's authoring rules. Separate item; §5 D9.
- **Bumping the Cauchy anchor to OKF v0.2.** A `CauchyIO/linear` change, not an awow one.
- **A conformance validator in the payload.** Per §4.6.
- **Enriching a documentation-poor repo.** `adopting-okf` already refuses to invent content; so does the wizard's offer.

## 5. Decisions taken (walkthrough of 2026-09-16)

Numbering preserved from the draft for traceability.

0. **Remit: verdict only.** awow adds the verdict, offers adoption at registration, fills the entrypoint, and owns no write path into the repo bundle; a developer adding an ADR is ordinary development, guided by one pointer to the adopt skill's Verify list. — Overrides the draft's premise; §1, §3, §4 rewritten to it.
1. **Repo side = recognised documentation with a declared bundle root (a).** One knowledge base, one ritual; every piece reused.
2. **Declaration = `knowledge:` key in the root `AGENTS.md` connector; anchor record entrypoint is the read-side copy (a).** One committed file the hook already parses, no anchor round-trip to know your own docs, fits CAU-1515's one-PR direction.
3. **Adopt existing docs at registration, otherwise nothing; awow never creates a bundle root later.** Honours `jit-context`'s stub-is-worse-than-absence rule; replaces the draft's "first capture creates the root".
4. **Default folder — moot.** No write path, so no default to choose; the adopt skill works on what exists.
5. **Every gate that inherits the reflex honours the verdict; its disposition is always reference-only (a, minus any write).** Parent §5.3 centralises the seam; a verdict honoured in some gates and not others is a seam that drifts.
6. **Story reference = default-branch blob URL built from the record's `resource` (a).** Clickable and unambiguous on a board shared by several repos.
7. **Conformance tooling — moot.** No write path, so no write-path rules and no validator; conformance is the adopt skill's Verify step at adoption time, plus the pointer.
8. **OKF versions: read v0.1 and v0.2, write v0.2 fields wherever awow emits OKF, never rewrite `okf_version`; the anchor bump is a linear item (a).** Works against the one real anchor today.
9. **Shipped anchor KB skeleton as a bundle = separate follow-up (a).** Keeps this slice to the anchored-repo gap; the follow-up owns the *frontmatter-light* amendment.
10. **Session-start hook reads `knowledge:` and adds one clause to the connected-anchored message (a).** A few lines on an existing helper, one test, one file read saved per session.
11. **Removed.** The un-park trigger existed for approach C, which is declined.

## 6. Affected files

Prompt and contract surface (payload):

- `.agents/skills/using-awow/SKILL.md` — §Route canonical knowledge: the fourth verdict, one sentence.
- `.agents/skills/knowledge-source-routing/SKILL.md` — §Capture: the verdict row, its reference-only disposition, the no-bundle and broken-entrypoint cases, and the one-line Verify pointer.
- `.agents/skills/adopting-okf/SKILL.md` — §Boundaries: one sentence allowing invocation from the anchored track over the repo's own docs, with approval; the routed-read-only sentence stays.
- `context/tooling/knowledge-sources.md` — §Reference before capture: the verdict row; §Anchored-repo records: one line that `knowledge.entrypoint` copies the connector's `knowledge:` key.
- `.agents/commands/setup-awow.md` — Anchored track step 4 (adoption offer, `knowledge:` key, adopt-or-nothing) and step 5 (fill the record's `knowledge:` block; CAU-1519's fallback wording).
- `context/team/conventions/REQUIRED/output-discipline.md` (shipped seed) and `.agents/skills/workitem-write/SKILL.md` §3 — the reference form of §4.5.
- `hooks/session-start.py` — read `knowledge:`; one clause in `ANCHORED_CONNECTED`.

Docs:

- `SETUP.md` §The Anchored track and `guides/guide-setup-and-two-harnesses.md` — the optional adoption offer and the `knowledge:` key.
- `README.md` — one clause where the anchored paragraph names what a repo keeps.

Not touched, deliberately: `/kb-mine`, `/kb-synthesize`, `mining.md`, `synthesis.md`, `kb-inbox/README.md`, `context/tooling/knowledge-base.md`, and every command that presents a knowledge placement — they inherit the verdict through the reflex.

## 7. Story body, ready to lift

**Title:** Route repo-canonical knowledge in anchored repos to the repo's own OKF bundle
**Team:** Cauchyio · **Project:** none · **Labels:** `type:feature`, `area:process`

> awow recognises when a durable fact raised in an anchored-repo session is canonical to that repo, keeps it out of the anchor knowledge base, and points at the repo's OKF bundle instead — which registration now offers to adopt from the repo's existing docs and registers as the anchor record's entrypoint. awow writes nothing into the repo; capturing the fact there is the developer's ordinary work.
>
> ## Acceptance criteria
> - [ ] The anchored setup track offers once, gated, to adopt an existing docs folder as an OKF v0.2 bundle; on yes it records the root as `knowledge:` in the connector frontmatter and fills `knowledge.entrypoint` in the anchor record; with nothing to adopt it writes nothing and never creates a root later.
> - [ ] In a connected anchored repo, every durable-knowledge gate classifies a fact about the repo as repo-canonical and disposes reference-only: no anchor KB write, at most a one-line reference naming the bundle root by URI (or the repo `resource` when none is declared), plus a pointer to the adopt skill's Verify list.
> - [ ] The session-start connected message names the bundle root when `knowledge:` is present and is unchanged when it is absent.
> - [ ] A session acting from the anchor and routed into the same repo remains read-only; existing routing behaviour is unchanged.
> - [ ] `tests/setup-awow/` gains an anchored-registration scenario with and without docs to adopt, `tests/hooks/test_session_start.py` covers the new key, and the path-token, context-writes, harness-wiring, and payload-classification suites pass with no render drift.
>
> ## Reference
> - Design: `proposals/repo-canonical-verdict.md`, extending `proposals/canonical-knowledge-source-routing-design.md` §5.4
> - Decision, once landed: `context/knowledge-base/decisions/repo-canonical-verdict.md`

## 8. Verification

Deterministic:

- `tests/setup-awow/` — new scenario `anchored-register`: a fixture repo with a connector, a `docs/` folder of three Markdown files, and an inert anchor clone; `post()` asserts the connector gained `knowledge:`, the docs gained `type` and a root `index.md`, no document body changed, and nothing was written under the anchor fixture. A `no-docs` variant asserts no bundle root, no `knowledge:` key, and the outcome recorded in `setup-progress.md`.
- `tests/hooks/test_session_start.py` — the connected tier surfaces the bundle root when `knowledge:` is present and says nothing when absent; the pre-rename spoke fixture is unchanged.
- `tests/gather-tokens/` — the new prompt text uses `{PROJECT}` and `{ANCHOR}`, never a literal path.
- `tests/context-writes/test_context_writes.py` — `setup-awow` remains the only command that names the connector as a write target.
- `tests/harness/*/wiring.sh` — anchored deploy still checks payload plus connector; the new key is tolerated.
- `python tools/gather.py --check` — no drift across Claude Code, Codex, Pi, opencode, Copilot renderings.

Behavioural acceptance, exercised in the entra repo (CAU-1280) before the story closes:

1. Registration over entra's existing docs produces a bundle and an entrypoint, and a linear session routes to it read-only.
2. A repo-specific decision stated in an entra session is classified repo-canonical: no anchor KB write, a reference to the bundle root, the Verify pointer; the developer adds the ADR by hand and it is reachable from the index.
3. The same fact raised in a linear session is classified external-canonical and becomes a reference, not a copy.
4. With the `knowledge:` key removed, the same gate references the repo and notes that no bundle is declared; it does not offer to create one.
5. A team convention stated in the entra session still routes to the anchor via `/update-context`, untouched by this change.

## 9. Relationship to existing work

- Extends the accepted routing design's reference-before-capture seam (§5.4) with one verdict and leaves §2.2's no-custody and §8's no-write-back exclusions intact — indeed relies on them to decline B′ and C.
- Completes what hub-and-spoke §3 left implicit: the spoke shape grows by one frontmatter key, not a folder or a pipeline.
- Sits beside `kb-capture-synthesize-spine.md` as the deliberate *non*-extension of its pipeline into repos; its Phase 4 stays about anchor feeders.
- Follows `jit-context`'s contract for the registration offer and for writing nothing when there is nothing to adopt.
- Absorbs CAU-1519's step-5 wording fix; aligns with CAU-1515's one-PR direction by keeping the repo's declaration in the repo.
- CAU-1280 (entra) is the first live test bed; CAU-1247 (linear's OKF v0.1 adoption) is the prior art behind D8 and the validator stance in §4.6.

*Landing note:* `proposals/.gitignore` is `*` with an allowlist, so this file is committed with `git add -f`, as the other proposals were.
