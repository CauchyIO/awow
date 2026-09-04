# Q3 stakeholder one-pager

## Intent

The export job now retries on transient failures and caps payloads at 10 MB, so nightly runs stop paging the on-call.

![Retry flow](diagram.png)

## Acceptance criteria

| Criterion | Status |
|---|---|
| Retry budget wired into the export job | done |
| Payload cap at 10 MB enforced | in review |
