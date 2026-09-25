# Retrospective Canon

This file is the canonical grounding for any retro-related work in this repo. The `/process-retro` skill reads it alongside `members.md` and `glossary.md`. Forks of the AWOW starter inherit it.

Practice, not theology — but if you want to know where the practice comes from, here it is.

---

## The Prime Directive

> "Regardless of what we discover, we understand and truly believe that everyone did the best job they could, given what they knew at the time, their skills and abilities, the resources available, and the situation at hand."

— Norm Kerth, *Project Retrospectives* (Dorset House, 2001)

**Function.** A pre-commitment device. By reading it aloud at the top of every retro, the team binds itself to a blameless frame *before* anything is revealed. The closest thing the field has to a constitutional clause.

**Operational rule for `/process-retro`.** If the transcript does not contain the Prime Directive (or a recognisable paraphrase) in its opening minutes, the report header flags this. Absence is itself signal — not punishable, but observable.

---

## The Five-Phase Model

Esther Derby & Diana Larsen, *Agile Retrospectives: Making Good Teams Great* (Pragmatic Bookshelf, 2006; 2nd edition with David Horowitz, 2024). Every commercial retro tool (Retrium, TeamRetro, Parabol, Neatro, EasyRetro) is structured around these phases.

| # | Phase | What happens | Handled by |
|---|---|---|---|
| 1 | **Set the Stage** | Purpose declared; Prime Directive read; working agreements; first-voice-in to break silence-as-consent | Team (human) |
| 2 | **Gather Data** | Surface facts, events, observations. Timeline, mood graphs, metrics. Shared reality *before* interpretation. | `/process-retro` §§ 1–5 |
| 3 | **Generate Insights** | "What does it mean?" Pattern-finding, root-cause, affinity mapping. | `/process-retro` §§ 8–9 |
| 4 | **Decide What to Do** | Small number of concrete, owned, dated experiments. | `/process-retro` §§ 6, 11 |
| 5 | **Close** | Appreciation. Meta-retro. Confirm next steps. | Team (human) |

**Discipline.** The phases must stay distinct. Premature jumping to solutions (phase 2 → phase 4) and unfiltered venting (phase 2 with no exit) are the two most common failure modes; both dissolve when phase boundaries are enforced.

**Operational rule.** `/process-retro` handles the middle three. It does not pretend to handle Set the Stage or Close — those are irreducibly human acts.

---

## Format Taxonomy

A retrospective format is the *activity* that fills the Gather Data and Generate Insights phases. Most named formats are interchangeable as long as the underlying phase discipline holds. Use canonical names where they exist.

### Open discussion
Continuous conversation without a silent phase. Often paired with a sticky-note template (Mad/Sad/Glad, Plus/Delta) for structure. Sensible default for young teams that need to vent before they can think. Risk: dominated by the loudest voices.

### Silent generation + walk-through
Solo writing on cards, then a structured walk-through. The template that fills the silence matters:

- **Mad / Sad / Glad** — three columns; folkloric early-2000s agile.
- **Plus / Delta** — two columns; folkloric, pre-agile, minimum-viable retro.
- **Starfish** — keep / less / more / stop / start. Patrick Kua, 2006 ([thekua.com](https://thekua.com/rant/2006/03/the-retrospective-starfish/)).
- **4Ls** — liked / learned / lacked / longed-for. Mary Gorman & Ellen Gottesdiener, EBG Consulting.
- **KALM** — keep / add / less / more. Community variant of Starfish.
- **DAKI** — drop / add / keep / improve. Community variant.
- **Sailboat / Speedboat** — boat metaphor with anchors, wind, rocks, island. Luke Hohmann, *Innovation Games* (2006).
- **Timeline** — co-construct a visual timeline. Derby & Larsen, *Agile Retrospectives* (2006).

When `/process-retro` detects silent-generation, it should also identify *which* template was used — the choice is itself signal about team maturity.

### 1-2-4-All
Solo (1 min) → pairs (2 min) → fours (4 min) → full group. Henri Lipmanowicz & Keith McCandless, *The Surprising Power of Liberating Structures* (2014). What most teams informally call "silent stickies then discussion" — the structured form has a name. Strong default for mixed introvert/extrovert teams.

### TRIZ (anti-problem)
"List everything you could do to *guarantee* the worst possible outcome. Then identify which of those things we're already doing." Lipmanowicz & McCandless. Use when "what's wrong" produces silence but "how would we sabotage this" produces laughter and truth.

### Five Whys
Pick one issue. Ask "why" five times. Sakichi Toyoda, 1930s; formalised in the Toyota Production System by Taiichi Ohno. A *Generate Insights* technique, not a whole-retro format.

### Lean Coffee
Agenda-less. Participants propose topics; dot-vote; time-box; thumbs to continue or move on. Jim Benson & Jeremy Lightsmith, Seattle, 2009. For mature teams who already know what matters.

### Futurespective
Forward-looking. "Imagine it's six months from now and this project has failed catastrophically — what happened?" (premortem). Paulo Caroli & TC Caetano; underlying premortem technique from Gary Klein (HBR, 2007).

### Rotating activities
Vary the activity when the *signal* goes stale, not when the *format* gets boring. Derby & Larsen support this; novelty for novelty's sake is not endorsed.

### Consistent template
Same format every retro. Predictability is its own value for teams that need it; the canon supports this as long as the signal still arrives.

### Conversational dominance (not a choice, a pathology)
What *emerges* when one speaker holds the floor disproportionately. Named in Google's Project Aristotle (2012–2015) as a negative predictor of team effectiveness. The standard term is *conversational* or *sequential dominance*. `/process-retro` flags this; the next retro switches to a structure that compensates (1-2-4-All, silent generation, dot-voting).

### On personality-based facilitation
Folk wisdom about "introvert-friendly" or "analytical team" retro styles is widespread but weakly grounded. Engineering populations skew INTJ/INTP/ISTJ on MBTI — but MBTI itself has weak test-retest reliability. What the facilitation literature *does* support is that **written-first-then-spoken structures raise participation regardless of personality typing**. Use the structures, skip the labels.

---

## What "Good" Looks Like

The literature converges on a few signals. Use them; don't invent.

### Action-item closure rate
**The standard quantitative measure.** (Completed action items / total) × 100. Industry baselines: 40–50%, climbing to ~65% with visible tracking. Targets: 80%+. A retro that produces beautiful insights and zero behaviour change has failed, even if everyone enjoyed it.

`/process-retro` reports this as the headline number of the trajectory section (when prior retros are available).

### Conversational turn-taking equity
Project Aristotle's strongest predictor of team effectiveness. Nuance: research distinguishes *equal speaking time* from *turn-taking freedom*. The latter is what matters. The goal is **"no one is locked out,"** not "everyone speaks exactly equally."

### Psychological safety
Amy Edmondson (1999). Strongest predictor of team learning behaviour. Observable markers in a transcript: people admit mistakes without hedging; junior members challenge senior members; bad news travels fast; the same one or two people don't carry every difficult topic.

### ROTI — Return on Time Invested
At close, each participant rates the meeting 0–4. Quick, lossy, useful as a trend line over time. The lightest practical evaluation tool.

### Behaviour change vs. venting ritual
Named in the literature as an anti-pattern. Retros that surface complaints with no commitment to action train the team to expect catharsis rather than change. Clinical signal: action items from three retros ago that nobody can find.

---

## History — How We Got Here

- **1930s–1990s.** Toyota's *hansei* (self-reflection) and *kaizen* (continuous improvement). Sakichi Toyoda's Five Whys; Taiichi Ohno's formalisation of the Toyota Production System.
- **2001.** Norm Kerth publishes *Project Retrospectives* (Dorset House). Names the practice. Authors the Prime Directive.
- **2001+.** Scrum adopts the Sprint Retrospective as one of its canonical events.
- **2006.** Esther Derby & Diana Larsen publish *Agile Retrospectives*. The five-phase model.
- **2014.** Henri Lipmanowicz & Keith McCandless publish *The Surprising Power of Liberating Structures*. 1-2-4-All, TRIZ, Troika Consulting absorbed into the retro toolkit.
- **2024.** Derby, Larsen & Horowitz publish the second edition — remote/hybrid practice and post-pandemic experience.

---

## References

**Canonical books**
- Norm Kerth, *Project Retrospectives: A Handbook for Team Reviews* (Dorset House, 2001).
- Esther Derby & Diana Larsen, *Agile Retrospectives: Making Good Teams Great* ([Pragmatic Bookshelf, 2006](https://pragprog.com/titles/dlret/agile-retrospectives/)).
- Derby, Larsen & Horowitz, *Agile Retrospectives, Second Edition* ([2024](https://pragprog.com/titles/dlret2/agile-retrospectives-second-edition/)).
- Henri Lipmanowicz & Keith McCandless, *The Surprising Power of Liberating Structures* ([2014](https://www.liberatingstructures.com/)).
- Luke Hohmann, *Innovation Games* ([2006](https://www.lukehohmann.com/innovation-games/speed-boat)).

**Live references**
- [Prime Directive](https://retrospectivewiki.org/index.php?title=The_Prime_Directive) — retrospectivewiki.org
- [1-2-4-All](https://www.liberatingstructures.com/1-1-2-4-all/) — liberatingstructures.com
- [Project Aristotle](https://psychsafety.com/googles-project-aristotle/) — psychsafety.com
- [Edmondson on psychological safety](https://psychsafety.com/the-history-of-psychological-safety/) — psychsafety.com
- [Action-item completion rate as a metric](https://count.co/metric/action-item-completion-rate) — count.co
- [Retrium anti-patterns](https://www.retrium.com/ultimate-guide-to-agile-retrospectives/retrospective-anti-patterns) — retrium.com
- [21 Sprint Retro Anti-Patterns](https://dzone.com/articles/21-sprint-retrospective-anti-patterns) — Wolpers, DZone
- [ROTI](https://www.neatro.io/blog/retrospective-roti/) — neatro.io

**Adjacent**
- `anti-patterns.md` (sibling) — the named pathologies `/process-retro` probes for.
- `members.md` (in `team/`) — who's in the room, used for attribution.
- `glossary.md` (in `knowledge-base/`) — domain terms used for disambiguation.
