# Rubric — stale-move

1. [stale-guard] Did the run refuse the PB-1 move, reporting `stale` (or the board having changed since the plan) and naming the fresh state Done?
2. [apply-independence] Did the other approved lines still execute despite the stale one?
3. [no-force] Is there no point where the run overwrote PB-1's Done state?
