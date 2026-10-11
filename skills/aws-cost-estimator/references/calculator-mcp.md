# Driving the AWS Pricing Calculator MCP servers

Both servers use calculator.aws public endpoints. No AWS account or credentials.

- `aws-calculator` = AWS sample server (`sample-aws-pricing-calculator-mcp`). Builds, lints and saves estimates. Its `get_service_fields` returns a curated **catalog** (known-working `minimalConfig` plus `traps[]`) for well-tested services. This is the server that writes estimates.
- `aws-calculator-costs` = community server (`aws-calculator-mcp`). Use it **only** to read costs back: `refresh_estimate` and `generate_report`, which open the saved link in the machine's Chrome. It accepts any calculator.aws link, including ones the AWS sample saved.

Tool names below are as published; go by the tool list actually present if they differ.

## Standard sequence
1. `aws-calculator.search_services` – comma-separated names → service keys (`"EC2, RDS PostgreSQL, Application Load Balancer, NAT Gateway, S3"`).
2. `aws-calculator.get_service_fields` – comma-separated keys. Read `catalog.minimalConfig`, `catalog.required`, `catalog.traps`, and any `freeTierChoice`.
3. Build the `services` JSON array (shape below).
4. `aws-calculator.build_estimate` with `name` + `services` → `{sharable_url, aws_estimate_id, services}`.
   - Big or iterative estimates: `create_estimate` → `add_service` (repeat) → `validate_estimate` → `export_estimate`.
5. `aws-calculator-costs.generate_report` (`estimate_url`, `format: "markdown"`) → per-service monthly cost, ARR, configs. Or `refresh_estimate` for the totals only.
   - If unavailable: `aws-calculator.get_estimate_cost` (needs Playwright), else open the link in a browser tool and read "Total monthly cost".
6. To change an estimate later: `aws-calculator.import_estimate` (url, `format: "json"`) → edit → `build_estimate` again. Each export produces a new link; share the latest one.

## Service entry shape
```json
{
  "service": "ec2Enhancement",
  "group": "Web tier",
  "estimateFor": "optional template id (Free Tier choice, Cognito tier…)",
  "config": { "region": "ap-south-1", "description": "Web servers", "...": "fields" }
}
```
Parent services with sub-services (S3, SNS, Step Functions, SageMaker, Bedrock, AppSync, VPC items) are added by **child key** (e.g. `amazonS3Standard`, `standardTopics`, `transitGatewayVpc`). The server wraps them in the parent.

## Field value patterns
| Field type | Value |
|---|---|
| numericInput | plain string: `"1000"` |
| dropdown | an option **id** from get_service_fields, not a label you guess |
| frequency | `{"value":"5","unit":"millionPerMonth"}` (units vary per service: `perMonth`, `perHour`…) |
| fileSize / storage | `{"value":"100","unit":"gb|NA"}` or `"gb|month"`, as the field specifies |
| duration | `{"value":"730","unit":"hours"}` |
| data transfer | array with **all three** entries: INBOUND (`fromRegion`), OUTBOUND (`toRegion: "External"` for internet), INTRA_REGION; unit `gb_month` or `tb_month` |
| instance matrix (RDS, OpenSearch, SageMaker…) | wrapped: `{"columnFormIPM":{"value":[{"Instance Type":{"value":"db.t3.medium"}, …}]}}` |

## Common resources → service keys
Confirm unknown keys with `search_services`.

| Resource | Service key | Notes |
|---|---|---|
| EC2 instance | `ec2Enhancement` | `instanceType`, `workload` = **instance count**, `selectedOS`, `pricingStrategy` (`"ondemand"`, `"spot"`, or `{"model":"computeSavings","term":"1 Year","upfrontPayment":"None"}`). Omitted term defaults to **3 Year** – pass `"1 Year"` explicitly. Use the `utilization` field for part-time running; never fake it with a fractional count. |
| EBS volume | `amazonElasticBlockStore` | `storageType` full option id (e.g. `"Storage General Purpose gp3 GB Mo"`), `storageAmount`, `numberOfInstances`, gp3 IOPS ≥3000 / throughput ≥125 |
| RDS PostgreSQL | `amazonRDSPostgreSQLDB` | columnFormIPM with `Instance Type`, `Deployment Option` (`Single-AZ` / `Multi-AZ`), `TermType` `OnDemand`; `storageVolume` `"General Purpose-GP3"` |
| RDS MySQL / others | search "RDS MySQL" etc. | same matrix pattern as PostgreSQL |
| Application Load Balancer | `applicationLoadBalancer` | count **plus at least one LCU driver** (e.g. processed GB/hour), otherwise $0 |
| NAT Gateway | `networkAddressTranslationNatGatewayVpc` | choose **Regional** or classic field set and set the other set to `"0"`; manifest defaults are 5×3 gateways – never leave defaults |
| S3 Standard | `amazonS3Standard` (child of `amazonSimpleStorageServiceGroup`) | `s3StandardStorageSize` `{"value":"200","unit":"gb|month"}` |
| Data transfer | `aWSDataTransfer` | three-entry array as above |
| Lambda | `aWSLambda` | `durationOfEachRequest` bare string ms; ask about **Free Tier** (`estimateFor`) |
| Fargate | `awsFargate` | `vcpuPerTask` ∈ 0.25/0.5/1/2/4/8/16 |
| Transit Gateway | `transitGatewayVpc` | attachments + GB processed |
| EKS, ElastiCache, CloudWatch, CloudFront, Route 53, public IPv4, WAF | `search_services` | no curated catalog yet: rely on `get_service_fields` defaults and validate |

## Pitfalls that produce wrong totals
- **$0 service** = misnamed field, wrong unit, or missing driver field. The calculator ignores unknown fields silently. Re-check field ids from `get_service_fields`.
- Use the **highest `_vN`** variant when fields are versioned.
- Never accept manifest defaults for counts (NAT, ALB, nodes); set every quantity explicitly.
- Free Tier is **included by default** where offered; for production, set `estimateFor` to the exclude-Free-Tier template.
- Region goes in every service `config.region`.
- Lint verdict "read-only" or "frozen" → fix before export; such links can't be edited in the calculator.
- The summary monthly total from the calculator is authoritative; per-row values can lag. Re-run `refresh_estimate` once if rows show $0.
- Share links are public to anyone with the URL – keep names/descriptions free of sensitive info.

## Requirements on the user's machine
- Node.js 18+ (for `npx`). Both servers download on first run.
- Google Chrome (or Chromium on Linux) installed in its standard location, for `aws-calculator-costs` cost readback.
- Network access to calculator.aws and its CloudFront endpoints.
