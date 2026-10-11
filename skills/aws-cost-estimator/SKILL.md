---
name: aws-cost-estimator
description: Estimates, breaks down and optimizes AWS infrastructure costs using the official AWS Pricing Calculator (calculator.aws), and returns a shareable estimate link. Use when the user asks "how much will this cost on AWS", "estimate AWS cost", "create an AWS calculator estimate", "cost of this Terraform", "compare instance/region costs", "why is our AWS bill high", "reduce AWS spend", or shares an architecture, resource list, Terraform/CloudFormation/CDK files or an AWS bill export.
---

# AWS Cost Estimator

Price AWS infrastructure with the **official AWS Pricing Calculator (calculator.aws)**, explain where the money goes, and find savings. AWS only. No AWS account or credentials are ever needed.

All prices come from calculator.aws. Never quote a price from memory or invent unit prices; if the calculator can't be reached, say so instead of estimating by hand.

## Files in this skill
- `references/calculator-mcp.md` – how to drive the calculator MCP servers: tool sequence, service keys, config shapes, pitfalls. **Read before the first calculator call.**
- `references/line-items.md` – AWS charges people forget.
- `references/optimization.md` – savings playbook.
- `references/mcp-tools.md` – AWS Knowledge server and the opt-in account servers.
- `examples/webapp-prod.md` – a worked request → calculator services example.

## Tools (all credential-free)
| Server | Role |
|---|---|
| `aws-calculator` (AWS sample) | Look up service fields, **build and validate** the estimate, save it, return the calculator.aws share link |
| `aws-calculator-costs` | **Read back the actual costs** of a saved estimate (`refresh_estimate`, `generate_report`). Uses the Chrome installed on the machine |
| `aws-knowledge` | Check a service/instance family is available in the region; read AWS docs |

Fallbacks for reading costs, in order: `aws-calculator-costs.refresh_estimate` → `aws-calculator.get_estimate_cost` → open the share link in a browser tool (built-in browser or Chrome) and read the totals from the page → give the user the link and say the totals show when it's opened. Use the next fallback without comment if one fails.

If the `aws-calculator` tools are missing entirely, tell the user the AWS Pricing Calculator connection isn't available (needs Node.js 18+; see plugin README) and stop rather than estimating by hand.

## Workflow

### 1. Pick the mode
- **Estimate** – planned architecture or IaC → calculator estimate + share link.
- **Compare** – build one estimate per option (region, instance family, pricing model) and compare the totals.
- **Analyze** – existing bill → see step 7.

### 2. Collect inputs (max 3 questions, then default and state it)
| Input | Default |
|---|---|
| Region | us-east-1 (India users: suggest ap-south-1, Mumbai) |
| Hours | 730/month (24x7) |
| Environments | prod only |
| Pricing | On-demand |
| Free Tier | **Exclude** for production estimates (ask if it's a hobby/dev account) |
| Internet egress | ask; if unknown assume 100 GB/month and flag it |
| Currency | USD; convert to local currency only in the summary, stating rate + date |

### 3. Build the resource list
List every resource with quantity, size and usage. For Terraform map `aws_instance`, `aws_db_instance`, `aws_lb`, `aws_nat_gateway`, `aws_eks_cluster`, `aws_s3_bucket`, `aws_ebs_volume`, `aws_lambda_function`, autoscaling groups (min / desired / max → low / expected / high). Walk `references/line-items.md` and add implied items (NAT, data transfer, EBS on every instance, logs, Multi-AZ).
Optionally confirm regional availability with `aws-knowledge.get_regional_availability`.

### 4. Map to calculator services
Follow `references/calculator-mcp.md`:
1. `search_services` for any service key you don't know.
2. `get_service_fields` for every service you'll add (batch them). Start from its catalog `minimalConfig`, apply every `traps[]` note, use the highest `_vN` field version.
3. Put each resource in a `group` per tier or environment (e.g. "Web tier", "Data tier") and give each a clear `description`.

### 5. Build, validate, save
- Prefer `build_estimate` (one call). For large estimates use `create_estimate` → `add_service` → `validate_estimate` → `export_estimate`.
- Fix everything `validate_estimate` / lint reports before exporting; never export an estimate the linter says will render read-only or $0.
- Keep the returned **share link** – it is the deliverable and the source of truth.

### 6. Read costs and optimize
- Get the numbers with `aws-calculator-costs.generate_report` (markdown; per-service monthly cost) or `refresh_estimate` (summary). The calculator's summary monthly total is authoritative; if per-row values look stale or $0, re-run once, then trust the summary.
- A service showing $0 almost always means a config error: check the traps for that service, fix, re-export.
- Apply `references/optimization.md`. To quantify a saving, build an **optimized estimate** (e.g. Savings Plan pricing strategy, Graviton instance types, gp3, fewer NAT gateways) and compare the two calculator totals. Never compute savings from memorized percentages when the calculator can price the alternative.

### 7. Analyze mode (existing bill)
Ask the user to download a Cost Explorer CSV (Billing console → Cost Explorer → Download CSV) or a CUR / Data Exports file and attach it. Load it with pandas; group by service, linked account, region, tag and month. Show month-over-month trend, flag any service up >20%, report untagged spend %, list top 10 cost drivers and waste candidates. To price a proposed fix, build a calculator estimate of the new setup.
If the opt-in billing server is present (see `references/mcp-tools.md`), it can replace the CSV.

## Output
1. **Summary** – monthly + annual total (from the calculator), top cost driver, potential savings, key assumptions.
2. **Calculator link(s)** – current estimate, and optimized estimate if built.
3. **Assumptions** list.
4. **Cost breakdown table** – Group | Service | Description / config | Monthly cost (from the calculator report).
5. **Chart** – cost by group or service.
6. **Low / expected / high** when usage is uncertain (one estimate each, or note which inputs drive the range).
7. **Optimization table** – change | monthly saving (calculator-priced) | effort | risk – and the optimized total.

Long-lived outputs (budgets, models) → spreadsheet; stakeholder report → document/dashboard; otherwise answer inline.

## Rules
- Prices only from calculator.aws (or the opt-in AWS Pricing server). No hardcoded or remembered prices.
- Read-only: never buy, change or create anything in an AWS account.
- Figures are estimates; actual bills vary with usage, discounts, credits and taxes (e.g. 18% GST for India accounts) – say so once.
- Share links are public to anyone who has them: don't put account IDs, customer names or internal hostnames in estimate names or descriptions unless the user asks.
- Commitment (Savings Plans / RI) suggestions are options for the user to evaluate, not financial advice.
