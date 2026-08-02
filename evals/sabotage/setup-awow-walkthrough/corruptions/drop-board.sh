#!/usr/bin/env bash
grep -vi "github issues" context/team.md > context/team.md.tmp && mv context/team.md.tmp context/team.md
