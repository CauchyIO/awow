# Program portfolio view

One tier above the team boards: a ranked portfolio of initiatives against finite specialist capacity.

> **TL;DR** — The team tier clears the fog of *what's happening*. Up here the job is **allocation
> under constraint**, so the centre of gravity is the portfolio, not a board. Priority routes
> **down** to team boards as stories; size and progress roll **up** from them — that read-back is
> the resource management. The view exists so a manager-of-managers can see where capacity is
> contended and rebalance. It is a lens over the team boards, never a second source of truth.

Illustrative data throughout — a worked mockup of the tier, not a live report.

## The model in one rule

| Direction | Owned by | What moves |
| --- | --- | --- |
| Priority routes **down** | The program | *what*, *priority*, *who*, *sequence* — initiatives drop onto team boards as stories. |
| Size rolls **up** | The teams | *how big* (sizing) and *how* — sizes and progress roll back to the portfolio. |

Run this view over teams that aren't on awow boards and it has nothing to roll up.

## Capacity & contention

Who is on what, and whether they can carry it. Columns are initiatives, ranked left→right by
priority; rows are teams. `L` leads, `C` contributes.

| Team | I1 | I2 | I3 | I4 | I5 | I6 | I7 | Load vs cap |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Infrastructure | · | · | L | · | · | · | L | 78% · 2 initiatives |
| Architecture | C | · | · | · | C | · | · | 95% · 2 initiatives |
| Data Governance | · | L | · | C | · | L | · | 88% · 3 initiatives |
| BI & Analytics | · | C | · | L | · | C | · | 70% · 3 initiatives |
| Platform | C | C | C | C | L | · | C | **132% · 6 initiatives — over** |
| Security | L | · | C | · | C | C | C | **115% · 5 initiatives — over** |

Platform and Security carry almost everything; no team-level fix clears an over-capacity row.

## The portfolio

| # | Initiative | Lead · contributors | Score | State | Sizing | Done | Rolled up from | Why it reads that way |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Identity & SSO federation | Security · Platform, Architecture | 9.2 | At risk | Sized | 60% | 4 items · 3 boards | Platform at capacity — moving, but the delivery date is exposed. |
| 2 | Data governance & lineage | Data Governance · Platform, BI & Analytics | 8.7 | On track | Sized | 40% | 4 items · 3 boards | Foundation for #4 — sequenced first on purpose. |
| 3 | Cloud landing zone | Infrastructure · Security, Platform | 8.1 | Blocked | Sized | 25% | 3 items · 3 boards | Needs Security sign-off, but Security is committed to #1. A sequencing conflict the program owns. |
| 4 | Self-service BI layer | BI & Analytics · Data Governance, Platform | 6.9 | On track | Partly sized | 15% | 3 items · 3 boards | Waiting on #2's lineage before it can fully size — cross-initiative dependency. |
| 5 | API & integration mesh | Platform · Architecture, Security | 6.4 | At risk | Sized | 30% | 3 items · 3 boards | Architecture single-threaded across design reviews — a staffing call, not a team fix. |
| 6 | Regulatory reporting | Data Governance · BI & Analytics, Security | 5.8 | Not started | Unsized | 0% | 2 items · 2 boards | Allocated and prioritised; awaiting sizing at the next refinement. |
| 7 | DR & resilience | Infrastructure · Platform, Security | 4.9 | Not started | Unsized | 0% | 2 items · 2 boards | Lowest priority and its teams are the contended ones — proposed move to the next increment. |

### Where the numbers come from

Every figure rolls up from the team boards; nothing is re-keyed. Each row expands into the items
behind it — initiative 3, for example:

| Team | Board | Item | State |
| --- | --- | --- | --- |
| Infrastructure | Azure DevOps | INF-88 — Network landing zone | In progress |
| Security | Jira | SEC-160 — Guardrail policy sign-off | **Blocked** |
| Platform | Linear | PLT-318 — Subnet automation | Ready |

One card carries the whole **Blocked** flag; everything else is moving. The same drill-down explains
every state in the table above — *Partly sized* means one item is still an unestimated backlog card,
*Unsized* means only backlog cards exist, and a percentage is just the states of the items rolled up.

## Only the program can clear these

Not bugs and not stories, but **allocation decisions**: re-sequence, re-staff, or cut scope.

| # | Constraint | Why it can't be fixed below | The move |
| --- | --- | --- | --- |
| A1 | Platform is at 132% — six initiatives funnel through it. | It is the program's true constraint; the ranking is meaningless until its load is under 100%. | Defer #7 to the next increment → Platform drops to ~108%; then re-time #5 to land under capacity. |
| A2 | #3 blocked on Security sign-off while Security is committed to #1. | Two of the top three compete for the same Security capacity in the same window — a cross-initiative priority clash. | Sequence #1's sign-off ahead of #3, or pull in external Security review for #3. |
| A3 | Architecture is single-threaded across #1 and #5 design reviews. | One reviewer gates two initiatives' design gates; a staffing decision, not something the team can absorb. | Add a second reviewer for the increment, or stagger the two gates two weeks apart. |
| A4 | #4 can't fully size until #2 delivers lineage. | A forecast gap, not a block — fine as sequenced, but flag it so the dependency isn't read as a stalled team. | Watch: hold #4's commit until #2 hits 60%; revisit at the next plenary. |

The two tiers meet at the plenary, where teams see the ranked, allocated portfolio and commit.

## Sources of truth

- [`.agents/commands/okr-cascade.md`](../.agents/commands/okr-cascade.md) — the department-tier read across teams' quarterly docs that this view sits alongside
- [`.agents/commands/project-plan.md`](../.agents/commands/project-plan.md) — where the sequencing and dependency facts behind a ranking are stated
- `context/tooling/board.md` — the per-team board surfaces the roll-up reads; written by `/setup-awow`
- Companion guides: [two feedback loops + a plan↔execution bridge](guide-cross-team-and-pillar.md) — the mechanism that keeps this roll-up honest
