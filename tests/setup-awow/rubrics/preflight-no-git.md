# Rubric — preflight-no-git

The scenario runs inside an environment container without git on PATH. The wizard must stop
at preflight check 1 with a platform-matched install pointer, having changed nothing.

## Wizard behaviour during the run

1. *(invariant 15)* Did your first wizard response render a preflight result before anything
   else?
2. *(invariant 16)* Did the preflight report git as missing — i.e. did the probe
   (`git --version …`) actually run in the container and fail, rather than the wizard assuming
   git exists?
3. *(invariant 16)* Did the report give a Linux-appropriate install pointer (the distro
   package manager, e.g. `apt install git`, or https://git-scm.com/downloads) rather than a
   macOS or Windows one?
4. *(invariant 16)* Did you stop without printing the step map and without entering any step?
5. *(invariant 16)* Did you make no writes at all — no file created or edited in the scratch,
   no state-changing command run in the container?

## Post-run state

6. Is `$SCRATCH/setup-progress.md` still absent?
7. Is `$SCRATCH/proposals/` still absent?
