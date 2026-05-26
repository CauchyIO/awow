# Work-item archetypes distilled from the `entra` Linear sessions

**Date:** 2026-05-25 · **Source:** `mlflow_export/entra` — 324 traces / 26 sessions / user `casper`, working dir `/Users/casper/repos/entra`, repo `CauchyIO/entra`. 91 traces touched Linear (`mcp__linear-server__*`).

This report distills the *kinds of work item* you actually drove through Linear in that session set, to inform awow's archetype model ([[archetypes-board-anchoring]]). Proposed archetypes are at the top; methodology, evidence, and caveats follow so you can check every claim against the referenced issues.

---

## Proposed work-item archetypes (review these first)

Each row is a recurring *type* of work, with the discipline that distinguishes it and the issues that ground it. None of these is awow's shipped `bugfix` — the `entra` reality is identity/infra-as-code, and the archetype set reflects that.

| # | Archetype | One-line definition | Distinguishing discipline | Grounding issues |
|---|---|---|---|---|
| 1 | **identity-provisioning** | Onboard / offboard a person or principal across all platforms at once | Checklist-shaped "done" (account · license · groups · subscription · GitHub); multi-platform, idempotent | CAU-877, CAU-467, CAU-878, CAU-880 (branches `cau-877-onboard-kevin*`) |
| 2 | **access-grant / RBAC-change** | Grant, scope, or revoke a role or permission | Least-privilege + blast-radius reasoning ("what does this role inherit?") | CAU-448, CAU-449, CAU-463, CAU-878 |
| 3 | **desired-state-executor** | Implement a new IaC executor / DSL capability that reconciles config → platform | Declare-then-reconcile; tests against desired vs actual; the repo's "feature" shape | CAU-396, CAU-285, CAU-286, CAU-288, CAU-291, CAU-380, CAU-393 |
| 4 | **drift-reconciliation** | Fix divergence between declared config and live (portal-made) state | The "bug" is drift, not a code defect; ignore/import portal-derived attrs | CAU-879, CAU-877 (`ignore-portal-derived-user-attrs`), CAU-414 |
| 5 | **infra-hardening / destructive-change guardrail** | Add safety around destructive infra ops | `prevent_destroy`, no `-auto-approve`, safe-rename runbook, pre-apply CI gate | CAU-557 |
| 6 | **pipeline-setup** | Stand up CI/CD plan/apply, OIDC, remote state | Manual approval gate; per-module plan workflows; state backend | CAU-398, CAU-397, CAU-284, CAU-475 |
| 7 | **audit / assessment (spike)** | Read-only investigation → recommendation + follow-up tickets, no code deliverable | Time-boxed; output is a decision doc + spawned tickets | CAU-377, CAU-463, CAU-476, CAU-448, CAU-558, CAU-394 |
| 8 | **incident-forensics / RCA** | Reconstruct what happened from logs/state, name root cause, spawn remediation | Forensic timeline; deliverable is the analysis, fixes become separate tickets | CAU-414, CAU-473 |
| 9 | **board-shaping / issue-authoring** | Create a project, split an umbrella issue, open follow-up tickets | Decomposition + linkage; creation-side, not execution | CAU-317, CAU-876, CAU-880, CAU-285, CAU-558 |
| 10 | **license / cost-management** | Evaluate or change licensing/spend; often a decision or blocker | Cost evidence; frequently *blocks* other work rather than shipping code | CAU-381, CAU-473, CAU-286, CAU-558, CAU-476, CAU-880 |

**Strongest, most distinct candidates** (clear execution signal — own branch + `save_issue` + files modified): **identity-provisioning (1), desired-state-executor (3), infra-hardening (5), pipeline-setup (6)**. The rest are real but either read-heavy (7, 8), creation-side (9), or decision-shaped (10).

---

## The biggest finding: most Linear interaction was *not* work-item execution

The dominant interaction mode by volume was **navigation / status**, not "process this item":

- `list_issues` (34 calls) drove repeated rollups — *"on the linear board what issues are assigned to me and pending"*, *"What are some other issues pending in this project?"*, *"refresh me the overview now i am lost in your statements"*. A single such trace name-drops ~7 issue IDs in its response, which is why ~88 distinct CAU IDs appear but only ~25 show real execution signal.
- The next mode was **board-shaping** — *"Make it a project and refer these issues in it"* (CAU-317), *"move CAU-396 to done. What are the next issues? List them and I'll break them up"*, *"Can you make an issue of this… and assign it to me"* (CAU-876).
- Actual end-to-end *execution* of a single item (branch → code → PR → close) was the minority.

Implication for awow: the archetype model covers *executing* a work item, but your real Linear usage is weighted toward **orchestration** (status, triage, decomposition). That maps more to `/refinement-prep` (authoring/splitting) and a status/`daily-checkin`-style surface than to `/process-workitem`. Worth deciding whether archetypes should also describe these non-execution modes, or whether they belong to a different command.

---

## How this challenges awow's base archetype set

The proposal ([[archetypes-board-anchoring]]) listed example archetypes: `bugfix`, `column-add/schema-change`, `source-onboard`, `infra-change`, `doc`, `refactor`, `spike`, `api-change`. Against the `entra` evidence:

- **Direct hits:** `spike` → audit/assessment (7); `infra-change` → splits into the more useful **pipeline-setup (6)** and **infra-hardening (5)**; `doc` → minor here (CAU-821 annotations).
- **Not anticipated by the base set:** identity-provisioning, access-grant/RBAC, desired-state-executor, drift-reconciliation, incident-forensics, board-shaping, license/cost. These are the *majority* of real work.
- **`bugfix` barely appeared** as a clean defect. The closest analogue is drift-reconciliation (4), which is a different discipline (state divergence, not a code bug).

This is direct evidence for the thesis that **the shipped archetype set is a starting point a team must extend** — the `entra` team's real archetypes are almost entirely domain-specific and would be authored locally.

---

## Per-archetype evidence (references you can verify)

1. **identity-provisioning** — CAU-877 "onboard Kevin Casey Patyk": *"So now Kevin is functionally onboarded: ✅ Entra account ✅ M365 license ✅ Member of all 5 groups ✅ Azure Subscription Contributor ✅ GitHub org."* The checklist *is* the acceptance criteria. Spawned CAU-878/879/880. Branches: `cau-877-onboard-kevin-casey-patyk-in-entra`, `-fix-kevin-display-name`, `-display-name-and-github-trim`, `-ignore-portal-derived-user-attrs`. Files: `users.py`, `relations.py`, `access_policies.py`, `main.tf`.
2. **access-grant / RBAC** — CAU-448/449: *"There are a lot of VergenceContributor roles… keyvaults, storage accounts"* → reasoning about subscription-level Contributor inheritance. CAU-463 (Urgent): *"Review and scope down Azure RBAC assignments — too liberal for agent safety."* CAU-878: grant SP `User.ReadWrite.All`.
3. **desired-state-executor** — CAU-396 "implement desired-state IAM configuration using DSL" (the long-lived working branch). CAU-285 user provisioning from config, CAU-286 M365 license via Terraform, CAU-288 mailing-list/M365 executor, CAU-291 GitHub membership executor, CAU-380 Pydantic schema, CAU-393 testing strategy.
4. **drift-reconciliation** — CAU-879 "Fix `azuread_user` for terraform-driven user creation"; CAU-877 branch `ignore-portal-derived-user-attrs` (*"fastest clean fix"*); CAU-414 forensic shows config wanting to CREATE groups that already existed in the portal.
5. **infra-hardening** — CAU-557 "harden entra terraform against accidental M365 group destruction": *"prevent_destroy, safe-rename runbook, pre-apply CI check, no `-auto-approve`… the concrete cleanup from the March 28 incident."* Own branch `cau-557-harden-entra-terraform`.
6. **pipeline-setup** — CAU-398 "set up CI/CD pipeline for terraform plan/apply with manual gate" (OIDC, `terraform-plan.yml`/`terraform-apply.yml`); CAU-397 remote `azurerm` state backend; CAU-475 add `bootstrap-plan.yml`. CAU-284 is the umbrella that 397/398 were split out of.
7. **audit / assessment** — CAU-377 "Audit Linear workspace membership and roles"; CAU-476 "Assess Microsoft partner program path against 5-month Azure spend"; CAU-558 spend pull (2,435.85 EUR / 5mo) + recommendation; CAU-394 assessment of HR-document-storage deep research (GDPR three-layer model).
8. **incident-forensics / RCA** — CAU-414 & CAU-473: *"I have the complete forensic picture now… forensic timeline (March 28, 2026)… 09:27:17 Claude ran `terraform apply -auto-approve`… config wanted to CREATE m365_groups conflicting with existing groups."* The deliverable is the timeline; the fix became CAU-557.
9. **board-shaping / issue-authoring** — CAU-317 created project "Agentic Coding Course for Engineers"; *"move CAU-396 to done… List them and I'll break them up"*; CAU-876 created on request and assigned; CAU-880 opened as a follow-up.
10. **license / cost-management** — CAU-381 "License auto-purchase workflow (human-in-the-loop)"; CAU-473 "Evaluate Entra ID license tiers" (P1 gates group-based licensing — *blocked* CAU-285/286); CAU-880 "Restore group-based licensing."

---

## Methodology & caveats (so you can weigh the assessment)

- **Extraction:** parsed all 324 traces from the session JSONs. Pulled the user prompt (`mlflow.traceInputs`), the final response, the Linear span names, `git.branch`, and `files.modified` per trace; grouped by `CAU-\d+` IDs found in prompt/response. Scripts produced `/tmp/entra_byissue.txt` (per-issue) and `/tmp/entra_digest.txt` (per-trace).
- **Span attributes did not serialize** in this export (`_serialize_error: 'Span' object has no attribute to_json`). So I have Linear *action names* (`get_issue`, `save_issue`, `list_issues`, `save_comment`, `save_project`…) but **not** the tool payloads — no raw issue titles/bodies/labels. Issue *type* was inferred from your prompts, the assistant's responses, branch names, and files modified — strong, corroborating signals, but not the issue records themselves.
- **Count inflation:** the ~88 distinct CAU IDs overstate distinct *work*. Status-rollup traces name many IDs at once, so an ID can appear "touched" while only being listed. I separated issues with **execution signal** (own branch + `save_issue` + files modified) from those appearing only in rollups; the archetype grounding above favours the former.
- **Response text is truncated** to ~700 chars per issue in the digest, so nuance inside long issues may be missed. I did not open Linear or the `entra` repo directly — this is purely the trace export.
- **Confidence:** high for archetypes 1, 3, 5, 6 (clear branches + files); medium for 2, 4, 7, 8 (clear intent, less code signal); 9 and 10 are real interaction modes but arguably belong outside `/process-workitem`.

## Open questions for you

1. Which of these 10 do you consider *real archetypes worth authoring* vs. noise? My shortlist for authoring first: identity-provisioning, desired-state-executor, infra-hardening, pipeline-setup.
2. Do board-shaping (9) and the navigation/status mode belong to archetypes at all, or to `/refinement-prep` and a `/daily-checkin`-style surface?
3. Want me to pull the actual issue bodies (re-run an export with span attributes, or read Linear directly) to confirm the type inferences before any of these become handler files?
