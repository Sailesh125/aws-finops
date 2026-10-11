# AWS line items people forget

Walk this list for every estimate. Add a calculator service entry for each one the architecture implies.

## Networking
- **NAT Gateway** – hourly charge per gateway per AZ **plus** a per-GB data-processing charge. Private subnets with internet access almost always need one per AZ in prod.
- **Internet egress** – data transfer out to the internet (first 100 GB/month free across the account, then tiered).
- **Inter-AZ transfer** – billed in both directions (~$0.01/GB each way). Multi-AZ apps, cross-AZ DB reads, and Kafka/ES replication generate a lot of it.
- **Inter-region transfer** – replication, cross-region backups, DR.
- **Public IPv4 addresses** – every public IPv4 (EC2, ELB, NAT, RDS public) is billed hourly since Feb 2024.
- **VPC endpoints (interface)** – hourly per AZ + per-GB; gateway endpoints for S3/DynamoDB are free.
- **Transit Gateway / VPN / Direct Connect** – attachment hours + per-GB.

## Load balancing / edge
- **ALB/NLB** – hourly + LCU/NLCU usage.
- **CloudFront** – egress per GB + requests; often cheaper than direct EC2/S3 egress.
- **Route 53** – hosted zones + queries; health checks.
- **WAF** – web ACL + rules + per-million requests.

## Compute
- **EBS root volumes** on every EC2 / EKS node.
- **EKS control plane** – per cluster hour (extended support costs much more for old K8s versions).
- **Autoscaling** – estimate at min / desired / max.
- **Windows / RHEL / SQL Server licensing** built into the hourly rate.

## Storage & backup
- **EBS snapshots** and AMIs piling up.
- **gp2 vs gp3**, provisioned IOPS/throughput on io1/io2/gp3.
- **S3 requests** (PUT/GET) and lifecycle transition fees, not just GB stored.
- **AWS Backup** vaults and cross-region copies.

## Databases
- **RDS Multi-AZ doubles** instance cost (and storage).
- **Read replicas** are billed as separate instances.
- **Backup storage** beyond the free size of provisioned storage.
- **Aurora I/O** charges (Standard) vs Aurora I/O-Optimized.
- **RDS extended support** for old engine versions.

## Observability & security
- **CloudWatch Logs** ingestion (per GB) + storage; custom metrics; alarms; dashboards.
- **CloudTrail** extra trails / data events.
- **GuardDuty, Security Hub, Config** – per-event / per-rule charges.
- **Secrets Manager** per secret + API calls; **KMS** per key + requests.

## Account level
- **Support plan** – Business support is a % of monthly spend with a minimum.
- **Taxes** – e.g. 18% GST on India-billed accounts.
- **Credits / EDP / private pricing** reduce real cost – ask if the org has them.
