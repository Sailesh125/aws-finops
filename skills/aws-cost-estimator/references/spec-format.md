# Resource spec format (input to scripts/estimate.py)

```json
{
  "name": "Web app - prod",
  "region": "ap-south-1",
  "hours_per_month": 730,
  "currency": {"code": "INR", "rate": 83.5},
  "resources": [
    {"type": "ec2", "instance_type": "t3.medium", "count": 3, "os": "linux"},
    {"type": "ebs", "volume_type": "gp3", "size_gb": 30, "count": 3},
    {"type": "alb", "count": 1, "lcu": 2},
    {"type": "rds", "engine": "postgres", "instance_class": "db.t3.medium", "multi_az": true, "storage_gb": 100},
    {"type": "s3", "storage_gb": 200, "storage_class": "standard"},
    {"type": "nat_gateway", "count": 1, "processed_gb": 150},
    {"type": "data_transfer_out", "gb": 500},
    {"type": "public_ipv4", "count": 2},
    {"type": "cloudwatch_logs", "ingest_gb": 20},
    {"type": "eks", "clusters": 1},
    {"type": "lambda", "requests_millions": 5, "avg_ms": 200, "memory_mb": 512},
    {"type": "custom", "service": "Route 53", "description": "hosted zone", "monthly_cost": 0.5}
  ]
}
```

Supported `type` values: `ec2`, `ebs`, `ebs_snapshot`, `rds`, `s3`, `alb`, `nlb`, `nat_gateway`, `data_transfer_out`, `inter_az`, `public_ipv4`, `cloudwatch_logs`, `eks`, `lambda`, `elasticache`, `custom`.

Any resource can carry:
- `"unit_price": <number>` – override the built-in price (per hour for hourly items; per GB-month or per GB for storage/transfer).
- `"hours": <number>` – override hours for that resource (e.g. 250 for a dev box on business hours only).
- `"env": "dev"` – label used for per-environment subtotals.

Region handling: built-in prices are us-east-1. For other regions the script applies an approximate multiplier (e.g. ap-south-1 ≈ 1.05 for compute) and marks every line `approx.` Always verify key SKUs for non-us-east-1 regions.
