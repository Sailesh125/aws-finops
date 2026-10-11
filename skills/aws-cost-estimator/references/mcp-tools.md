# Other AWS MCP servers

The calculator servers are covered in `calculator-mcp.md`. This file covers the helper server and the opt-in account servers.

Tool names can change between server versions, so go by the tool list actually present in the session.

## AWS Knowledge MCP (`aws-knowledge`) – bundled, no credentials
Remote AWS-hosted server at `https://knowledge-mcp.global.api.aws`. No AWS account or login; rate-limited.

| Tool | Use |
|---|---|
| `get_regional_availability` | Confirm a service, instance family or CloudFormation resource exists in the target region before adding it to an estimate |
| `list_regions` | Map region codes ↔ names (ap-south-1 = Asia Pacific (Mumbai)) |
| `search_documentation` / `read_documentation` | Look up service limits, pricing dimensions or feature details to understand what to configure |

Not a price source: prices come from the calculator only. If this server is unreachable, skip the availability check and note it in the assumptions.

---
## Opt-in account servers (need AWS credentials)
Not loaded by default. The plugin's `optional/mcp-aws-account.json` adds them; use them only if their tools are already present in the session. Never ask the user for credentials to enable them.

### AWS Pricing MCP (`aws-pricing`)
Package `awslabs.aws-pricing-mcp-server` (uvx, `AWS_PROFILE`, IAM `pricing:*`). Gives raw Price List API prices and Terraform/CDK project scanning (`analyze_terraform_project`, `analyze_cdk_project`). Useful to cross-check one SKU, or to scan an IaC folder for services; the calculator estimate remains the deliverable.

### AWS Billing & Cost Management MCP (`aws-billing-cost-management`)
Package `awslabs.billing-cost-management-mcp-server`. Read-only billing IAM permissions (`optional/iam-policy.json`). Cost Explorer API calls cost about $0.01 each; keep queries focused (monthly, 3–6 months, one group-by at a time).

| Capability | Typical tool | Use |
|---|---|---|
| Historical cost & usage | `get_cost_and_usage` | Analyze mode instead of a CSV export |
| Anomalies | `get_anomalies` | Flag spikes |
| Budgets | `describe_budgets` | Budget vs actual |
| Savings Plans / RI recs | `get_savings_plans_purchase_recommendation`, `get_reservation_purchase_recommendation` | Size commitments, then price them in the calculator |
| Rightsizing | `get_ec2_instance_recommendations` | Pick target instance types, then price them in the calculator |
| Cost Optimization Hub | `list_recommendations` | Consolidated savings list |

Rules: read-only; never purchase commitments or change budgets. If Compute Optimizer or Cost Optimization Hub report "not enrolled", say so and use the playbook. Mask account IDs in shareable output.

## Without the opt-in servers
| Need | Credential-free route |
|---|---|
| Prices | AWS Pricing Calculator MCP (`calculator-mcp.md`) |
| Region availability | `aws-knowledge.get_regional_availability` |
| Real spend | User attaches a Cost Explorer CSV or CUR export |
| Commitment sizing | Build a Savings Plan variant in the calculator, sized to the steady baseline |
| Rightsizing | Ask for CloudWatch CPU/memory p95, or flag as "needs utilization data" |
