# MCP catalogue and intake

Approved MCP servers, plus the intake template used to assess new ones.

## Catalogue

See `catalogue.md` for the team's approved-MCP list. Add entries via the intake form.

## Intake

When the team wants to add a new MCP, run through the intake template (`intake-template.md`, landing in v0.2). Until then, the questions to answer:

- **Author and publisher.** Who built this MCP?
- **Exposed tools.** What tools does it expose to the agent?
- **Tool behaviour.** Read or write? Side effects?
- **Blast radius.** Worst-case outcome if the agent calls every tool with adversarial inputs?
- **Data flow.** Personal data? Credentials? Leaves the org boundary?
- **Security precautions.** Auth, access control, rate limiting, logging?

The intake answers go in `mcps/intake/<MCP-name>.md`. A reviewer (security lead + architect) approves or rejects. Approved MCPs are added to `catalogue.md`.

## Reference

- The full reference: see the intake-template and rollout-playbook tickets in the team's upstream research inventory — these are the source for the v0.2 versions.
- MCP Servers Directory: see `REFERENCES.md`. Cross-reference, don't vendor.
