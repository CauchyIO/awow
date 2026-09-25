#!/bin/sh
# join-anchored: a configured anchored repo on a machine that has no .awow/anchor.json yet;
# anchor-checkout/ stands in for the local clone of the anchor.
set -e
git init -q "$1"
git -C "$1/anchor-checkout" init -q
git -C "$1/anchor-checkout" remote add origin https://github.com/example-team/anchor.git
git -C "$1/anchor-checkout" add -A
git -C "$1/anchor-checkout" -c user.name=fixture -c user.email=fixture@example.invalid commit -qm "anchor fixture"
exit 0
