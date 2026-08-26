#!/bin/sh
# preflight-not-a-repo: the scratch must NOT be a git repository.
rm -rf "$1/.git"
exit 0
