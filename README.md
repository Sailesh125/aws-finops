# aws-finops

A Claude plugin that estimates, analyzes and optimizes AWS infrastructure costs using the **official AWS Pricing Calculator** ([calculator.aws](https://calculator.aws)).

Describe your setup or share Terraform, and Claude builds a real calculator.aws estimate. You get back a **shareable estimate link**, a cost breakdown, and savings options priced by the calculator.

**No AWS account, login or credentials needed.**

## What's inside
| Component | Needs AWS credentials? | Purpose |
|---|---|---|
| Skill: `aws-cost-estimator` | No | Workflow: gather inputs, map resources to calculator services, build the estimate, read costs, recommend savings |
| MCP: `aws-calculator` ([aws-samples/sample-aws-pricing-calculator-mcp](https://github.com/aws-samples/sample-aws-pricing-calculator-mcp), MIT-0) | No | Builds, validates and saves estimates on calculator.aws; returns the share link |
| MCP: `aws-calculator-costs` ([Musheer360/aws-calculator-mcp](https://github.com/Musheer360/aws-calculator-mcp), MIT) | No | Reads back the calculator's actual dollar figures from a saved estimate (uses your installed Chrome) |
| MCP: `aws-knowledge` (AWS-hosted) | No | Checks whether a service or instance type is available in a region; AWS docs |
| `optional/` | Yes, opt-in only | AWS Pricing API and Billing & Cost Management servers for live account data. Not loaded unless you add them. |

## Requirements
- **Node.js 18+**, which provides `npx`. Both calculator servers download automatically on first use.
- **Google Chrome**, installed in its standard location, so costs can be read back. Chromium also works on Linux. Without Chrome you still get the estimate link; the totals show when you open it.
- Internet access to calculator.aws.

## Example prompts
- "Estimate the monthly AWS cost for 3 t3.medium servers behind an ALB, Postgres db.t3.medium Multi-AZ, 200 GB S3, in Mumbai, and give me the calculator link."
- "What will this Terraform cost?" (attach the `.tf` files)
- "Compare on-demand vs a 1-year Compute Savings Plan for this setup."
- "Here's our Cost Explorer CSV. Why did the bill go up?"

## How it works
1. Claude lists your resources and adds commonly forgotten items (NAT, data transfer, EBS, Multi-AZ).
2. It looks up each service's exact calculator fields, then builds and validates the estimate with `aws-calculator`.
3. The estimate is saved to calculator.aws, which gives a share link.
4. `aws-calculator-costs` opens the link in headless Chrome and reads the calculator's per-service and total costs.
5. For savings, Claude builds an optimized estimate (Savings Plans, Graviton, gp3…) and compares the two totals.

All prices come from calculator.aws; the plugin has no built-in price list.

## Use with GitHub Copilot
The same skill and calculator servers also work as a **Copilot custom agent**.

| File | Used by |
|---|---|
| `.github/agents/aws-cost-estimator.agent.md` | Custom agent profile for Copilot cloud agent (github.com), Copilot CLI, and VS Code |
| `.github/skills/aws-cost-estimator` | The skill: a link to `skills/aws-cost-estimator`, which Copilot loads automatically |
| `.vscode/mcp.json` | The calculator MCP servers for VS Code agent mode. VS Code ignores `mcp-servers` in agent profiles, so it needs this file. |

**In this repo:** open it in VS Code, start the MCP servers from `.vscode/mcp.json`, then pick **aws-cost-estimator** in the Copilot Chat agent picker. In Copilot CLI, run `/agent`. On github.com, pick it in the agents panel or when assigning Copilot to an issue.

**In your own app repo (shift-left):** copy these three into the repo where your Terraform lives:
```
.github/agents/aws-cost-estimator.agent.md
.github/skills/aws-cost-estimator/      (copy the real folder: skills/aws-cost-estimator)
.vscode/mcp.json
```
Then ask, for example, *"@aws-cost-estimator what will the Terraform in infra/ cost per month? Give me the calculator link."*

Alternatively, install the skill once for all your projects by copying `skills/aws-cost-estimator` to `~/.copilot/skills/`.

**Copilot cloud agent notes:**
- The agent profile sets up the MCP servers itself.
- The cloud agent's firewall must allow `calculator.aws`, the calculator's CloudFront endpoints, and `registry.npmjs.org` (for `npx`). Add them in the repo's Copilot settings if calls are blocked.
- If the runner has no Chrome, cost readback falls back to giving you the estimate link.

**Windows:** `.github/skills/aws-cost-estimator` is a git symlink. If your clone shows it as a small text file, copy `skills/aws-cost-estimator` there instead, or enable `git config core.symlinks true`.

## Version pinning
The servers are pinned to the versions this plugin was written against: `sample-aws-pricing-calculator-mcp@1.3.3` and `aws-calculator-mcp@2.3.1`. To upgrade, change the versions in `.mcp.json` and re-test.

## Optional: live account data (needs AWS credentials)
See `optional/`:
- `mcp-aws-account.json` adds the AWS Labs Pricing and Billing & Cost Management servers.
- `iam-policy.json` is a least-privilege, read-only policy for them.

To enable them: install [uv](https://docs.astral.sh/uv/getting-started/installation/), configure an AWS profile, attach the policy, merge the server entries into `.mcp.json`, and set `AWS_PROFILE`.

## Notes and limits
- Calculator share links are public to anyone who has the URL. Keep estimate names free of sensitive details.
- The calculator servers use calculator.aws endpoints that AWS doesn't document, so they may break when AWS changes the calculator. The AWS sample server describes itself as sample code.
- Figures are estimates. Actual bills vary with usage, discounts, credits and taxes (e.g. 18% GST).
- The skill is read-only: it never buys or changes anything in AWS.

## Sources
- AWS Pricing Calculator: https://calculator.aws
- sample-aws-pricing-calculator-mcp: https://github.com/aws-samples/sample-aws-pricing-calculator-mcp
- aws-calculator-mcp: https://github.com/Musheer360/aws-calculator-mcp
- AWS Knowledge MCP Server: https://awslabs.github.io/mcp/servers/aws-knowledge-mcp-server
