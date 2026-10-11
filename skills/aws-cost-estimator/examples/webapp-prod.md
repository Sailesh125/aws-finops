# Example: 3-tier web app in Mumbai

**User:** "Estimate 3 t3.medium web servers behind an ALB, Postgres db.t3.medium Multi-AZ with 100 GB, 200 GB S3, one NAT gateway, 500 GB/month internet egress, in Mumbai. Production."

**Assumptions stated:** ap-south-1, 24x7, on-demand, Free Tier excluded, 30 GB gp3 root volume per server, NAT processes ~150 GB/month, ALB ~2 GB/hour processed.

**Calls:**
1. `aws-calculator.get_service_fields` with `service: "ec2Enhancement, amazonElasticBlockStore, applicationLoadBalancer, amazonRDSPostgreSQLDB, amazonS3Standard, networkAddressTranslationNatGatewayVpc, aWSDataTransfer"`. Check catalog configs and traps.
2. `aws-calculator.build_estimate` with `name: "Web app - prod (ap-south-1)"` and `services` set to the array below.
3. `aws-calculator-costs.generate_report` with `estimate_url: <sharable_url>` and `format: "markdown"`.

```json
[
  {"service": "ec2Enhancement", "group": "Web tier",
   "config": {"region": "ap-south-1", "description": "Web servers", "instanceType": "t3.medium",
              "workload": 3, "selectedOS": "linux", "pricingStrategy": "ondemand"}},
  {"service": "amazonElasticBlockStore", "group": "Web tier",
   "config": {"region": "ap-south-1", "description": "Root volumes gp3 30 GB", "numberOfInstances": "3",
              "durationOfInstanceRuns": {"value": "730", "unit": "hours"},
              "storageType": "Storage General Purpose gp3 GB Mo",
              "storageAmount": {"value": "30", "unit": "gb|NA"},
              "gp3Iops": "3000", "gp3Throughput": {"value": "125", "unit": "mbps"}, "snapshotFrequency": "0"}},
  {"service": "applicationLoadBalancer", "group": "Web tier",
   "config": {"region": "ap-south-1", "description": "Public ALB", "numberOfApplicationLoadBalancers": "1",
              "sizeOfDataProcessedForEC2InstanceAndIPAddressTargets": {"value": "2", "unit": "gb|hour"}}},
  {"service": "amazonRDSPostgreSQLDB", "group": "Data tier",
   "config": {"region": "ap-south-1", "description": "Postgres Multi-AZ",
              "columnFormIPM": {"value": [{"Number of Nodes": {"value": "1"},
                                           "Instance Type": {"value": "db.t3.medium"},
                                           "Deployment Option": {"value": "Multi-AZ"},
                                           "TermType": {"value": "OnDemand"},
                                           "undefined": {"value": {"unit": "100", "selectedId": "%Utilized/Month"}}}]},
              "storageVolume": "General Purpose-GP3",
              "storageAmount": {"value": "100", "unit": "gb|NA"}}},
  {"service": "amazonS3Standard", "group": "Data tier",
   "config": {"region": "ap-south-1", "description": "Assets bucket",
              "s3StandardStorageSize": {"value": "200", "unit": "gb|month"}}},
  {"service": "networkAddressTranslationNatGatewayVpc", "group": "Network",
   "config": {"region": "ap-south-1", "description": "NAT gateway",
              "numberOfGateways": "1", "dataProcessedPerNATGateway": {"value": "150", "unit": "gb|month"},
              "regionalNatGatewayCount": "0", "regionalNatGatewayAzCount": "0",
              "regionalNatGatewayDataProcessed": {"value": "0", "unit": "gb|month"}}},
  {"service": "aWSDataTransfer", "group": "Network",
   "config": {"region": "ap-south-1", "description": "Internet egress",
              "dataTransfer": {"value": [
                {"entryType": "INBOUND", "value": "0", "unit": "gb_month", "fromRegion": "External"},
                {"entryType": "OUTBOUND", "value": "500", "unit": "gb_month", "toRegion": "External"},
                {"entryType": "INTRA_REGION", "value": "0", "unit": "gb_month"}]}}}
]
```

**Optimized variant (build as a second estimate and compare totals):** EC2 with `pricingStrategy: {"model":"computeSavings","term":"1 Year","upfrontPayment":"None"}`, or `t4g.medium` (Graviton). Also consider Single-AZ for a non-prod copy of the DB.

**Answer shape:** summary with the calculator total, both links, a breakdown table from `generate_report`, a chart by group, and a savings table priced from the optimized estimate.

> This config follows the server's catalog as of v1.3.3. Always re-check with `get_service_fields`; field ids can change when AWS updates the calculator.
