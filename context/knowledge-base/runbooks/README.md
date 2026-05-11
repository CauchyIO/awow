# context/knowledge-base/runbooks/

Step-by-step operational procedures. On-call response, common ops, incident response, recurring manual steps.

A runbook is *testable* — anyone on the team can follow the steps and produce the expected outcome. If a step is "use your judgement here", that's not a runbook step yet.

## Template

```markdown
# <Procedure name>

## When to run this
<Trigger conditions.>

## Prerequisites
- <Access / tools / credentials needed>

## Steps
1. <Specific action>
2. <Specific action>
3. <Verification: how to know the step worked>

## On failure
<What to do if a step fails.>

## Owner
<Team / role responsible for keeping this runbook current.>
```

## What does NOT live here

- One-off scripts → the codebase
- Patterns / architectural shapes → `patterns/`
- Decisions about *whether* to do something → `decisions/`
