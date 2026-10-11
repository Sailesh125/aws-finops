# Using AWS MCP servers

Tool names can change between server versions, so go by the tool list and descriptions actually present in the session. Names below are the documented ones.

## 0. AWS Knowledge MCP (`aws-knowledge`) – default, no credentials
Remote AWS-hosted server at `https://knowledge-mcp.global.api.aws`. No AWS account or login; rate-limited.

| Tool | Use in workflow |
|---|---|
| `get_regional_availability` | Step 4: confirm a service, instance family or CloudFormation resource exists in the target region before pricing it |
| `list_regions` | Map region codes ↔ names (e.g. ap-south-1 = Asia Pacific (Mumbai)) |
| `search_documentation` | Find the official pricing page or doc for a service or feature |
| `read_documentation` | Read an aws.amazon.com / docs.aws.amazon.com page as markdown, e.g. a pricing page, to verify a price |

Tips:
- It does not return prices directly. Pricing pages that load prices with JavaScript may come back without the price table; if so, fall back to web search for the SKU + region price and cite the result.
- If rate-limited or unreachable, continue with built-in prices and web search.

---
The two servers below are **opt-in only**. They need AWS credentials and are not loaded by default; use them only if their tools are already present in the session.

## 1. AWS Pricing MCP (`aws-pricing`) – opt-in
Package: `awslabs.aws-pricing-mcp-server`, launched with `uvx`, uses `AWS_PROFILE`. IAM: `pricing:*` (Price List API calls are free).

| Capability | Typical tool | Use in workflow |
|---|---|---|
| List services with pricing | `get_pricing_service_codes` | Find service codes: `AmazonEC2`, `AmazonRDS`, `AmazonS3`, `AWSELB`, `AmazonEKS`, `AWSLambda`, `AmazonVPC`, `AmazonCloudWatch`, `AmazonElastiCache` |
| Discover filter attributes | `get_pricing_service_attributes`, `get_pricing_attribute_values` | Find exact attribute values (e.g. `instanceType`, `databaseEngine`, `deploymentOption`) before querying |
| Get prices | `get_pricing` | Step 4: price each distinct SKU in the target region |
| Bulk price lists | `get_price_list_urls` | Only for large comparisons |
| Scan IaC | `analyze_terraform_project`, `analyze_cdk_project` | Step 3: cross-check the resource spec |
| Cost report | `generate_cost_report` | Optional extra; still run `estimate.py` for the canonical table |

Tips:
- Region filter uses the region code (e.g. `ap-south-1`); some queries use the location name ("Asia Pacific (Mumbai)").
- EC2 on-demand Linux filters: `instanceType`, `operatingSystem=Linux`, `tenancy=Shared`, `preInstalledSw=NA`, `capacitystatus=Used`.
- RDS: `instanceType`, `databaseEngine` (PostgreSQL/MySQL/...), `deploymentOption` (Single-AZ/Multi-AZ). If you fetch the Multi-AZ price directly, don't also double it — set `unit_price` on the rds resource and `multi_az` only affects the storage line.
- Filters can return several SKUs; pick the one matching the exact spec and on-demand term, and sanity-check against the built-in table (a 10× difference means the wrong SKU).
- Write fetched prices into the spec as `"unit_price"` so the calculator shows `override` as the source; report them as "live (AWS Price List, <date>)".

## 2. AWS Billing & Cost Management MCP (`aws-billing-cost-management`) – opt-in
Package: `awslabs.billing-cost-management-mcp-server`. Needs AWS credentials with read-only billing permissions (plugin file `optional/iam-policy.json`). Cost Explorer API calls cost about $0.01 each — keep queries focused (monthly granularity, 3–6 months, grouped by one dimension at a time).

| Capability | Typical tool | Use in workflow |
|---|---|---|
| Historical cost & usage | `get_cost_and_usage` (Cost Explorer) | Analyze mode: trend by SERVICE, LINKED_ACCOUNT, REGION, TAG |
| Anomalies | `get_anomalies` | Flag spikes |
| Budgets | `describe_budgets` | Show budget vs actual |
| Savings Plans recs | `get_savings_plans_purchase_recommendation` | Step 5 commitments (use 1-yr, no upfront, 30-day lookback as default) |
| RI recs | `get_reservation_purchase_recommendation` | RDS / ElastiCache / OpenSearch commitments |
| Rightsizing | `get_ec2_instance_recommendations` (Compute Optimizer) | Step 5 rightsizing |
| Cost Optimization Hub | `list_recommendations` | Consolidated savings list |
| Free tier / credits | `get_free_tier_usage`, `get_credits` | Adjust net cost |

Rules:
- Read-only. Never purchase commitments or change budgets, even if a tool allows it.
- Compute Optimizer and Cost Optimization Hub must be opted in on the account; if they return "not enrolled", say so and fall back to the playbook.
- Mask account IDs in anything shareable.

## Credential-free fallback summary
| Need | Without AWS credentials |
|---|---|
| Unit prices | Built-in table in `estimate.py`, verified via AWS Knowledge `read_documentation` or web search on aws.amazon.com/pricing |
| Region availability | AWS Knowledge `get_regional_availability` |
| Real spend | Ask for a Cost Explorer CSV or CUR export |
| Commitment sizing | `references/optimization.md` percentages, sized to steady baseline |
| Rightsizing | Ask for CloudWatch CPU/memory p95, or flag as "needs utilization data" |
