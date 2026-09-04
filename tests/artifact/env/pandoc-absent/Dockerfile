# pandoc-absent: a Linux machine without pandoc on PATH. The RUN guard fails
# the build if the base image ever starts shipping pandoc, so the scenario
# can't silently rot into testing nothing.
FROM debian:bookworm-slim
RUN if command -v pandoc >/dev/null 2>&1; then echo "base image ships pandoc — pick a slimmer base" >&2; exit 1; fi
