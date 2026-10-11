---
name: aws-cost-estimator
description: Estimates, breaks down and optimizes AWS infrastructure costs. Use when the user asks "how much will this cost on AWS", "estimate AWS cost", "why is our AWS bill high", "reduce AWS spend", "cost of this Terraform", "compare instance/region costs", or shares an architecture, resource list, Terraform/CloudFormation/CDK files or an AWS bill (CUR / Cost Explorer export).
---

# AWS Cost Estimator

Estimate what AWS infrastructure costs (or will cost), explain where the money goes, and find savings. AWS only.

Inputs can be: a plain-English architecture, a resource list, Terraform / CloudFormation / CDK code, an architecture diagram, or a billing export (Cost and Usage Report CSV, Cost Explorer CSV, invoice PDF).

## Files in this skill
- `scripts/estimate.py` – offline calculator. Takes a JSON resource spec, prints a cost table, category totals and a JSON result.
- `references/mcp-tools.md` – how to use the credential-free AWS Knowledge MCP, plus the opt-in account servers.
- `references/line-items.md` – checklist of AWS charges people forget.
- `references/optimization.md` – savings playbook with typical percentages.
- `references/spec-format.md` – the JSON spec the script accepts.
- `examples/webapp-prod.json` – sample spec (3-tier web app in ap-south-1).

## Step 0 – Detect data sources (silently)
This skill must work with **no AWS account and no AWS credentials**. Never ask the user for AWS keys, a profile, or IAM access.

Default (credential-free) sources, in order:
1. **Built-in prices** in `scripts/estimate.py` – always available, approximate.
2. **AWS Knowledge MCP** (`aws-knowledge`, no auth) – confirm a service/instance family exists in the target region (regional availability, region list) and read official AWS docs and pricing pages as markdown.
3. **Web search / fetch** of official AWS pricing pages (aws.amazon.com/<service>/pricing) to verify the biggest line items.

Opt-in sources – use only if their tools are already present in this session (the user added `optional/mcp-aws-account.json` themselves):
- `aws-pricing` MCP – exact prices via the AWS Price List API.
- `aws-billing-cost-management` MCP – real account spend and recommendations.

If a tool is missing or errors, move on to the next source without comment. Don't suggest the opt-in servers unless the user asks for real account data or exact live prices.

Read `references/mcp-tools.md` before the first MCP call.

## Workflow

### 1. Pick the mode
- **Estimate** – planned architecture → projected monthly/annual cost.
- **Analyze** – existing account/bill → explain spend, trends, waste.
- **Compare** – two architectures, regions, or pricing models side by side.

### 2. Collect inputs (max 3 questions, then default and state it)
| Input | Default |
|---|---|
| Region | us-east-1 (India users: suggest ap-south-1, Mumbai) |
| Hours | 730/month (24x7) |
| Environments | prod only |
| Pricing | On-demand |
| Currency | USD; also convert to local currency if known, stating rate + date |
| Internet egress | ask; if unknown assume 100 GB/month and flag it |

### 3. Build the resource spec
Translate the input into the JSON format in `references/spec-format.md`. For Terraform, map `aws_instance`, `aws_db_instance`, `aws_lb`, `aws_nat_gateway`, `aws_eks_cluster`, `aws_s3_bucket`, `aws_ebs_volume`, `aws_lambda_function`, autoscaling groups (min / desired / max → low / expected / high). If the opt-in Pricing MCP is present, also run its Terraform/CDK project analysis to catch services the manual mapping missed.
Walk through `references/line-items.md` and add anything implied but missing (NAT, public IPv4, logs, snapshots, multi-AZ doubling).

### 4. Price it
- **Default (no credentials):** start from built-in prices. For the top 3–5 cost lines, or any region other than us-east-1, verify the on-demand price from the official pricing page (AWS Knowledge `read_documentation`, or web fetch/search). Write each verified price into the spec as `"unit_price"` and cite the page and date. Leave the rest `approx.`
- If AWS Knowledge `get_regional_availability` shows an instance family or service isn't offered in the region, say so and suggest the nearest equivalent.
- **Opt-in Pricing MCP present:** fetch exact prices for every distinct SKU instead, source `live (AWS Price List)`.

Then always run the calculator so the arithmetic is done in code:
```
python ${CLAUDE_PLUGIN_ROOT}/skills/aws-cost-estimator/scripts/estimate.py spec.json --json out.json
```
(If `${CLAUDE_PLUGIN_ROOT}` isn't set, use the path of this skill folder.)

### 5. Optimize
Apply `references/optimization.md`. If the opt-in Billing MCP is present, also pull Savings Plan / RI purchase recommendations, Compute Optimizer EC2 recommendations and Cost Optimization Hub items, and prefer those real numbers over playbook percentages. For each recommendation: change, est. monthly saving, effort (L/M/H), risk, source. Rank by saving ÷ effort. Re-run the calculator on the optimized spec for the optimized total.

### 6. Analyze mode (existing account)
- **Default (no credentials):** ask the user to download a Cost Explorer CSV (Billing console → Cost Explorer → Download CSV) or a CUR / Data Exports file and attach it. Load it with pandas; group by service, linked account, region, tag and month.
- **Opt-in Billing MCP present:** get cost and usage for the last 3–6 months the same way; get anomalies; describe budgets; check credits.

Show month-over-month trend, flag any service up >20%, report untagged spend %, list top 10 cost drivers and waste candidates (idle EC2, unattached EBS, old snapshots, idle load balancers, unused public IPv4).

## Output
1. **Summary** – monthly + annual total, top cost driver, potential savings, key assumptions.
2. **Data sources** – which prices were verified from official pages (with date) vs built-in approximations.
3. **Assumptions** list.
4. **Cost breakdown table** – Category | Service | Resource | Qty | Usage | Unit price | Monthly cost | Price source.
5. **Chart** – cost by category (and monthly trend for Analyze mode).
6. **Low / expected / high** when usage is uncertain.
7. **Optimization table** and **optimized total**.
8. **Sources** – pricing pages or MCP tools used, with date.

Long-lived outputs (budgets, models) → spreadsheet; stakeholder report → document/dashboard; otherwise answer inline.

## Rules
- Read-only: never create, modify or purchase anything in the AWS account (no buying Savings Plans/RIs, no budget changes). Recommendations only.
- Always say figures are estimates; actual bills vary with usage, discounts, credits, and taxes (e.g. 18% GST for India accounts).
- Do arithmetic in code, not prose.
- Use correct AWS terms: Compute Savings Plans vs EC2 Instance Savings Plans vs Reserved Instances.
- Commitment suggestions are cost-model inputs for the user to decide on, not financial advice.
- Don't print account IDs, ARNs or invoice numbers in shareable outputs unless the user asks.
