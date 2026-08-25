# Rubric — preflight-not-a-repo

The scratch is not a git repository. The wizard must stop at preflight check 2 with a
pointer, having changed nothing.

## Wizard behaviour during the run

1. *(invariant 15)* Did your first wizard response render a preflight result before anything
   else?
2. *(invariant 16)* Did the preflight report that the workspace is not a git repository?
3. *(invariant 16)* Did the report tell the user how to fix it (run `git init` there, or cd
   to the intended repository)?
4. *(invariant 16)* Did you stop without printing the step map and without entering any step?
5. *(invariant 16)* Did you avoid running `git init`, and avoid offering to run it yourself?
6. *(invariant 16)* Did you make no writes at all — no file created or edited in the scratch,
   no state-changing Bash call?

## Post-run state

7. Is `$SCRATCH/.git/` still absent?
8. Is `$SCRATCH/setup-progress.md` still absent?
