# preflight-no-git: a Linux machine without git on PATH — the one preflight
# environment the host suite can never produce (every dev machine has git).
# The RUN guard fails the build if the base image ever starts shipping git,
# so the scenario can't silently rot into testing nothing.
FROM debian:bookworm-slim
RUN if command -v git >/dev/null 2>&1; then echo "base image ships git — pick a slimmer base" >&2; exit 1; fi
