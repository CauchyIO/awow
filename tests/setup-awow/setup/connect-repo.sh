#!/bin/sh
# connect-repo: the scratch is the repo being connected; anchor-checkout/ inside it stands in
# for a local clone of the anchor, with an origin that matches the --anchor URL.
set -e
git init -q "$1"
git -C "$1/anchor-checkout" init -q
git -C "$1/anchor-checkout" remote add origin https://github.com/example-team/anchor.git
git -C "$1/anchor-checkout" add -A
git -C "$1/anchor-checkout" -c user.name=fixture -c user.email=fixture@example.invalid commit -qm "anchor fixture"
exit 0
