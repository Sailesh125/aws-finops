# AWS savings playbook

Typical savings below are only for picking which levers to try. The saving you report must come from the calculator: build the optimized setup as a second estimate and compare its total with the original.

How to model each lever in the calculator: Savings Plans and Spot via the EC2 `pricingStrategy` field; Graviton by changing `instanceType` (t4g, m7g, c7g, r7g, db.*g); gp2 → gp3 via `storageType`; shutting environments down at night via EC2 `utilization`, or fewer hours; S3 tiering by moving GB to IA or Glacier child services; NAT savings by reducing NAT data processed (and adding the free S3/DynamoDB gateway endpoints).

| # | Lever | Applies to | Typical saving | Effort | Risk |
|---|---|---|---|---|---|
| 1 | Rightsize over-provisioned instances (CPU p95 < 40%) | EC2, RDS, ElastiCache | 20–50% of that resource | L–M | Low |
| 2 | Delete idle / unattached resources (EBS, EIPs, old snapshots, idle ELBs) | Account-wide | 100% of the waste | L | Low |
| 3 | Compute Savings Plan (1-yr no upfront) for steady baseline | EC2, Fargate, Lambda | ~25–30% (3-yr: up to ~50–66%) | L | Commitment |
| 4 | EC2 Instance Savings Plan / Reserved Instances | Fixed instance family | up to ~40% 1-yr, ~60–72% 3-yr | L | Less flexible |
| 5 | RDS / ElastiCache / OpenSearch Reserved Instances | Databases | ~30–40% 1-yr | L | Commitment |
| 6 | Graviton (arm64: t4g, m7g, c7g, r7g, db.*g) | EC2, RDS, ElastiCache, Lambda | ~20% price + better perf | M | App compat |
| 7 | Spot instances (Karpenter / ASG mixed) | Stateless, batch, CI, dev EKS nodes | up to 70–90% | M | Interruptions |
| 8 | Schedule non-prod off nights & weekends | Dev/staging EC2, RDS | ~65% of those envs | L | Low |
| 9 | gp2 → gp3 EBS | All EBS | ~20% | L | Low |
| 10 | S3 lifecycle to IA / Glacier / Intelligent-Tiering | Cold data | 40–90% of storage cost | L | Retrieval fees |
| 11 | S3/DynamoDB gateway VPC endpoints instead of NAT | NAT processed GB | Removes NAT per-GB for that traffic | L | Low |
| 12 | Keep traffic in one AZ where possible; zone-aware routing | Inter-AZ transfer | Varies | M | Availability trade-off |
| 13 | CloudFront in front of S3/ALB | Egress | 10–40% of egress + caching | M | Low |
| 14 | Cut log verbosity, set retention (e.g. 30 days), send to S3 | CloudWatch Logs | 30–70% | L | Low |
| 15 | Multi-AZ only for prod DBs | RDS non-prod | 50% of those DBs | L | Low for non-prod |
| 16 | Lambda memory tuning / ARM | Lambda | 10–40% | L | Low |
| 17 | Aurora I/O-Optimized when I/O > ~25% of Aurora bill | Aurora | Varies | L | Low |
| 18 | Release unused public IPv4, use IPv6 / private | Public IPv4 | $3.65/IP/month | L | Low |
| 19 | Upgrade off extended-support versions (EKS, RDS) | EKS, RDS | Removes surcharge | M–H | Upgrade risk |

## How to present
- One row per recommendation: change → est. monthly saving (USD + local currency) → effort → risk.
- Order by saving ÷ effort.
- Show "current total", "optimized total", and "% saving".
- Commitments (Savings Plans / RIs): size only to the steady baseline (e.g. the minimum of last 30 days' usage), never the peak. State these are options for the team to evaluate.
