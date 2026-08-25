#!/bin/sh
# clean-clone fixture decoy — the scenario's script declines the installer,
# so this file's presence is the signal and it must never execute during a
# run. Exiting loudly makes an accidental invocation unmissable.
echo "clean-clone fixture decoy installer — this must never run" >&2
exit 1
