# tests/awow-lock

A **code-level** regression test for `tools/awow_lock.py` — the 3-way lockfile
engine behind `/update-awow`. Unlike `tests/setup-awow/` (agent-behaviour
rubrics run through a harness), this is a plain stdlib `unittest`: no pytest, no
network, no LLM. It only needs Python and `git`.

```
python3 tests/awow-lock/test_awow_lock.py
```

It builds two throwaway git repos (upstream + local), diverges them so every
verdict fires at once — update / keep-local / conflict / skip / removed-local /
new — then asserts `apply` takes upstream where safe, **never overwrites a local
edit**, writes the `.awow` conflict sidecar, bumps the recorded version, and
converges on a second run.
