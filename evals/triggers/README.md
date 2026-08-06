# Trigger-eval corpus (T2)

Does the right skill fire for a given user utterance, in a given workspace state?
Each case is one headless session turn; detection is mechanical from the
transcript (which skill invocation appears, or none). This directory is the
corpus format and seed cases only — automated execution lands with the
trigger-detection check in a later PR.

Case fields: `utterance` (natural phrasing, typos welcome), `workspace` (fixture
the session starts in — trigger behaviour is state-dependent), `expected` (a
skill name, `none`, or an accepted set for genuinely ambiguous cases),
`category` (direct-positive | paraphrase | near-miss-negative | confusion-pair |
buried-intent | state-dependent), `provenance` (hand-seeded | mined), `weight`
(mined field cases count more than synthetic ones).

Scoring: per-skill precision/recall plus a confusion matrix; over-trigger and
under-trigger rates reported separately — they have different product
consequences (annoyance vs invisibility).
