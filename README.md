# aws-finops

Estimate, analyze and optimize AWS infrastructure costs with Claude.

**No AWS account, login or credentials needed.** Install and use it right away.

## What's inside
| Component | Needs AWS credentials? | Purpose |
|---|---|---|
| Skill: `aws-cost-estimator` | No | Estimate cost of a planned architecture or Terraform/CDK code, analyze an exported bill, compare options, recommend savings |
| Built-in calculator (`estimate.py`) | No | Does all the arithmetic offline with approximate on-demand prices |
| MCP: `aws-knowledge` (AWS-hosted) | No | Official AWS docs and pricing pages, region list, and whether a service or instance family is available in a region |
| `optional/` folder | Yes – opt-in only | Two extra AWS servers for exact live prices and real account spend. Not loaded unless you add them. |

## Example prompts
- "Estimate the monthly AWS cost for 3 t3.medium servers behind an ALB, Postgres db.t3.medium Multi-AZ, 200 GB S3, in Mumbai."
- "What will this Terraform cost?" (attach the `.tf` files)
- "Here's our Cost Explorer CSV. Why did the bill go up?"
- "Find the top 5 ways to cut this setup's cost."
- "Compare ap-south-1 vs us-east-1 for this setup."

## How prices work without credentials
1. The calculator starts from a built-in table of approximate us-east-1 on-demand prices, scaled for other regions. Those lines are marked `approx.`
2. For the biggest cost lines, Claude checks the official AWS pricing page (through the AWS Knowledge server or web search) and uses the verified price, citing the page and date.
3. Analyzing an existing bill? Download a CSV from the AWS Billing console (Cost Explorer → Download CSV) and attach it. No API access needed.

## Optional: exact live prices and real account data (needs AWS credentials)
Only if you want it. Files are in `optional/`:
- `mcp-aws-account.json` – adds the AWS Labs **Pricing** and **Billing & Cost Management** servers.
- `iam-policy.json` – least-privilege read-only policy for them.

To enable: install [uv](https://docs.astral.sh/uv/getting-started/installation/), configure an AWS profile (`aws configure --profile finops`), attach the policy, then merge the two server entries from `optional/mcp-aws-account.json` into the plugin's `.mcp.json` and set `AWS_PROFILE`. The skill picks them up automatically when present and ignores them when absent.

## Costs & safety
- The default setup makes no calls to your AWS account.
- The AWS Knowledge server is free to use but rate-limited.
- The skill stays read-only: it never buys Savings Plans/RIs or changes anything in AWS.
- Figures are estimates; actual bills vary with usage, discounts, credits and taxes (e.g. 18% GST).

## Sources
- AWS Knowledge MCP Server: https://awslabs.github.io/mcp/servers/aws-knowledge-mcp-server
- AWS Pricing MCP Server (optional): https://awslabs.github.io/mcp/servers/aws-pricing-mcp-server
- AWS Billing and Cost Management MCP Server (optional): https://awslabs.github.io/mcp/servers/billing-cost-management-mcp-server
