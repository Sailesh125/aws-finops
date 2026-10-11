#!/usr/bin/env python3
"""
AWS cost estimator.

Usage:
    python estimate.py spec.json [--json out.json] [--live]

Needs no AWS credentials. --live is an optional extra that queries the AWS
Price List API for EC2/RDS and only works where boto3 + AWS credentials exist;
without them it silently uses the built-in prices.

Reads a resource spec (see references/spec-format.md), prices every resource,
prints a markdown cost table plus category/env totals, and optionally writes JSON.

Built-in prices are APPROXIMATE us-east-1 on-demand Linux prices. Verify key SKUs
on https://aws.amazon.com/pricing before sharing final numbers. Use "unit_price"
in the spec to override any line.
"""
import argparse
import json
import sys
from collections import defaultdict

# ---------------------------------------------------------------------------
# Approximate us-east-1 on-demand prices (USD). Update as needed.
# ---------------------------------------------------------------------------
EC2_HOURLY = {
    "t3.micro": 0.0104, "t3.small": 0.0208, "t3.medium": 0.0416, "t3.large": 0.0832,
    "t3.xlarge": 0.1664, "t3.2xlarge": 0.3328,
    "t4g.micro": 0.0084, "t4g.small": 0.0168, "t4g.medium": 0.0336, "t4g.large": 0.0672,
    "m5.large": 0.096, "m5.xlarge": 0.192, "m5.2xlarge": 0.384, "m5.4xlarge": 0.768,
    "m6i.large": 0.096, "m6i.xlarge": 0.192, "m6i.2xlarge": 0.384,
    "m7i.large": 0.1008, "m7i.xlarge": 0.2016,
    "m6g.large": 0.077, "m6g.xlarge": 0.154, "m7g.large": 0.0816, "m7g.xlarge": 0.1632,
    "c5.large": 0.085, "c5.xlarge": 0.17, "c5.2xlarge": 0.34,
    "c6i.large": 0.085, "c6i.xlarge": 0.17, "c7g.large": 0.0725, "c7g.xlarge": 0.145,
    "r5.large": 0.126, "r5.xlarge": 0.252, "r6i.large": 0.126, "r6g.large": 0.1008,
    "r7g.large": 0.1071,
}
RDS_HOURLY = {  # single-AZ, PostgreSQL/MySQL
    "db.t3.micro": 0.018, "db.t3.small": 0.036, "db.t3.medium": 0.072, "db.t3.large": 0.145,
    "db.t4g.micro": 0.016, "db.t4g.small": 0.032, "db.t4g.medium": 0.065, "db.t4g.large": 0.129,
    "db.m5.large": 0.178, "db.m5.xlarge": 0.356, "db.m6g.large": 0.159, "db.m6i.large": 0.178,
    "db.m7g.large": 0.168, "db.r5.large": 0.25, "db.r6g.large": 0.225, "db.r7g.large": 0.239,
}
ELASTICACHE_HOURLY = {
    "cache.t3.micro": 0.017, "cache.t3.small": 0.034, "cache.t3.medium": 0.068,
    "cache.t4g.small": 0.032, "cache.t4g.medium": 0.065,
    "cache.m6g.large": 0.149, "cache.r6g.large": 0.206,
}
EBS_GB_MONTH = {"gp3": 0.08, "gp2": 0.10, "io1": 0.125, "io2": 0.125, "st1": 0.045, "sc1": 0.015}
S3_GB_MONTH = {"standard": 0.023, "intelligent_tiering": 0.023, "standard_ia": 0.0125,
               "onezone_ia": 0.01, "glacier_ir": 0.004, "glacier": 0.0036, "deep_archive": 0.00099}
P = {
    "ebs_snapshot_gb": 0.05,
    "rds_storage_gb": 0.115,      # gp2
    "alb_hour": 0.0225, "alb_lcu_hour": 0.008,
    "nlb_hour": 0.0225, "nlb_nlcu_hour": 0.006,
    "nat_hour": 0.045, "nat_gb": 0.045,
    "egress_gb": 0.09, "egress_free_gb": 100,
    "inter_az_gb": 0.02,          # 0.01 each direction
    "ipv4_hour": 0.005,
    "cw_logs_gb": 0.50,
    "eks_hour": 0.10,
    "lambda_req_million": 0.20, "lambda_gb_s": 0.0000166667,
}
# Rough multipliers vs us-east-1 (compute-ish). Mark as approx.
REGION_MULT = {
    "us-east-1": 1.0, "us-east-2": 1.0, "us-west-2": 1.0, "us-west-1": 1.17,
    "ap-south-1": 1.05, "ap-south-2": 1.05, "ap-southeast-1": 1.2, "ap-southeast-2": 1.2,
    "ap-northeast-1": 1.25, "eu-west-1": 1.1, "eu-central-1": 1.15, "eu-west-2": 1.15,
    "sa-east-1": 1.55, "me-south-1": 1.2,
}
REGION_NAMES = {  # for the Price List API "location" filter
    "us-east-1": "US East (N. Virginia)", "us-east-2": "US East (Ohio)",
    "us-west-1": "US West (N. California)", "us-west-2": "US West (Oregon)",
    "ap-south-1": "Asia Pacific (Mumbai)", "ap-south-2": "Asia Pacific (Hyderabad)",
    "ap-southeast-1": "Asia Pacific (Singapore)", "ap-southeast-2": "Asia Pacific (Sydney)",
    "ap-northeast-1": "Asia Pacific (Tokyo)", "eu-west-1": "EU (Ireland)",
    "eu-central-1": "EU (Frankfurt)", "eu-west-2": "EU (London)",
}


# ---------------------------------------------------------------------------
# Optional live pricing via AWS Price List API
# ---------------------------------------------------------------------------
class LivePricer:
    def __init__(self, region):
        import boto3  # noqa: F401  (raises ImportError if missing)
        self.client = boto3.client("pricing", region_name="us-east-1")
        self.location = REGION_NAMES.get(region)
        if not self.location:
            raise ValueError(f"no Price List location name for {region}")

    def _first_price(self, service, filters):
        resp = self.client.get_products(
            ServiceCode=service,
            Filters=[{"Type": "TERM_MATCH", "Field": k, "Value": v} for k, v in filters.items()],
            MaxResults=10,
        )
        for item in resp.get("PriceList", []):
            prod = json.loads(item)
            for term in prod.get("terms", {}).get("OnDemand", {}).values():
                for dim in term["priceDimensions"].values():
                    usd = float(dim["pricePerUnit"].get("USD", 0))
                    if usd > 0:
                        return usd
        return None

    def ec2(self, itype, os_="Linux"):
        return self._first_price("AmazonEC2", {
            "instanceType": itype, "location": self.location, "operatingSystem": os_,
            "tenancy": "Shared", "preInstalledSw": "NA", "capacitystatus": "Used"})

    def rds(self, iclass, engine="PostgreSQL", multi_az=False):
        return self._first_price("AmazonRDS", {
            "instanceType": iclass, "location": self.location, "databaseEngine": engine,
            "deploymentOption": "Multi-AZ" if multi_az else "Single-AZ"})


ENGINE_NAMES = {"postgres": "PostgreSQL", "mysql": "MySQL", "mariadb": "MariaDB",
                "aurora-postgresql": "Aurora PostgreSQL", "aurora-mysql": "Aurora MySQL"}


# ---------------------------------------------------------------------------
def price_resource(r, hours_default, mult, live):
    """Return list of line dicts for one resource spec."""
    t = r["type"]
    hours = r.get("hours", hours_default)
    env = r.get("env", "prod")
    override = r.get("unit_price")
    lines = []

    def add(category, service, resource, qty, usage, unit, unit_price, source="approx."):
        if override is not None and len(lines) == 0:
            unit_price, source = override, "override"
        cost = qty * usage * unit_price
        lines.append(dict(category=category, service=service, resource=resource, qty=qty,
                          usage=round(usage, 3), unit=unit, unit_price=round(unit_price, 6),
                          monthly_cost=round(cost, 2), env=env, source=source))

    if t == "ec2":
        it = r["instance_type"]; n = r.get("count", 1)
        up, src = None, "approx."
        if live:
            try:
                up = live.ec2(it, "Windows" if r.get("os") == "windows" else "Linux"); src = "live"
            except Exception as e:  # pragma: no cover
                print(f"[warn] live EC2 price failed for {it}: {e}", file=sys.stderr)
        if up is None:
            if it not in EC2_HOURLY and override is None:
                raise ValueError(f"Unknown EC2 type {it}: add unit_price to spec")
            up = EC2_HOURLY.get(it, 0) * mult; src = "approx."
        add("Compute", "EC2", it, n, hours, "hrs", up, src)

    elif t == "ebs":
        vt = r.get("volume_type", "gp3")
        add("Storage", "EBS", f"{vt} {r['size_gb']} GB", r.get("count", 1), r["size_gb"],
            "GB-mo", EBS_GB_MONTH[vt] * mult)

    elif t == "ebs_snapshot":
        add("Storage", "EBS Snapshots", "snapshots", 1, r["size_gb"], "GB-mo", P["ebs_snapshot_gb"] * mult)

    elif t == "rds":
        ic = r["instance_class"]; multi = r.get("multi_az", False); n = r.get("count", 1)
        engine = ENGINE_NAMES.get(r.get("engine", "postgres"), "PostgreSQL")
        up, src = None, "approx."
        if live:
            try:
                up = live.rds(ic, engine, multi); src = "live"
            except Exception as e:  # pragma: no cover
                print(f"[warn] live RDS price failed for {ic}: {e}", file=sys.stderr)
        if up is None:
            if ic not in RDS_HOURLY and override is None:
                raise ValueError(f"Unknown RDS class {ic}: add unit_price to spec")
            up = RDS_HOURLY.get(ic, 0) * mult * (2 if multi else 1); src = "approx."
        label = f"{ic} {engine}{' Multi-AZ' if multi else ''}"
        add("Database", "RDS", label, n, hours, "hrs", up, src)
        if r.get("storage_gb"):
            override = None  # override applies only to the instance line
            add("Database", "RDS", f"storage {r['storage_gb']} GB", n, r["storage_gb"], "GB-mo",
                P["rds_storage_gb"] * mult * (2 if multi else 1))

    elif t == "elasticache":
        nt = r["node_type"]
        if nt not in ELASTICACHE_HOURLY and override is None:
            raise ValueError(f"Unknown ElastiCache node {nt}: add unit_price")
        add("Database", "ElastiCache", nt, r.get("count", 1), hours, "hrs",
            ELASTICACHE_HOURLY.get(nt, 0) * mult)

    elif t == "s3":
        sc = r.get("storage_class", "standard")
        add("Storage", "S3", sc, 1, r["storage_gb"], "GB-mo", S3_GB_MONTH[sc] * mult)

    elif t in ("alb", "nlb"):
        n = r.get("count", 1)
        add("Networking", t.upper(), "load balancer hours", n, hours, "hrs", P[f"{t}_hour"] * mult)
        override = None
        cap = r.get("lcu", 1)
        add("Networking", t.upper(), f"{cap} capacity units avg", n, hours * cap, "LCU-hrs",
            P["alb_lcu_hour" if t == "alb" else "nlb_nlcu_hour"] * mult)

    elif t == "nat_gateway":
        n = r.get("count", 1)
        add("Networking", "NAT Gateway", "gateway hours", n, hours, "hrs", P["nat_hour"] * mult)
        override = None
        if r.get("processed_gb"):
            add("Networking", "NAT Gateway", "data processed", 1, r["processed_gb"], "GB", P["nat_gb"] * mult)

    elif t == "data_transfer_out":
        billable = max(0, r["gb"] - (0 if r.get("no_free_tier") else P["egress_free_gb"]))
        add("Networking", "Data Transfer", "internet egress (after 100 GB free)", 1, billable, "GB",
            P["egress_gb"] * mult)

    elif t == "inter_az":
        add("Networking", "Data Transfer", "inter-AZ (both directions)", 1, r["gb"], "GB", P["inter_az_gb"])

    elif t == "public_ipv4":
        add("Networking", "VPC", "public IPv4 addresses", r.get("count", 1), hours, "hrs", P["ipv4_hour"])

    elif t == "cloudwatch_logs":
        add("Observability", "CloudWatch", "logs ingestion", 1, r["ingest_gb"], "GB", P["cw_logs_gb"] * mult)

    elif t == "eks":
        add("Containers", "EKS", "control plane", r.get("clusters", 1), hours, "hrs", P["eks_hour"])

    elif t == "lambda":
        reqs = r["requests_millions"]
        gb_s = reqs * 1e6 * (r.get("avg_ms", 100) / 1000) * (r.get("memory_mb", 128) / 1024)
        arm = 0.8 if r.get("arch") == "arm64" else 1.0
        add("Serverless", "Lambda", "requests", 1, reqs, "M req", P["lambda_req_million"])
        override = None
        add("Serverless", "Lambda", f"compute {r.get('memory_mb', 128)} MB", 1, gb_s, "GB-s",
            P["lambda_gb_s"] * arm)

    elif t == "custom":
        add(r.get("category", "Other"), r.get("service", "Custom"), r.get("description", ""),
            1, 1, "month", r["monthly_cost"], "given")

    else:
        raise ValueError(f"Unsupported resource type: {t}")
    return lines


def estimate(spec, use_live=False):
    region = spec.get("region", "us-east-1")
    hours = spec.get("hours_per_month", 730)
    mult = REGION_MULT.get(region, 1.1)
    live = None
    if use_live:
        try:
            live = LivePricer(region)
        except Exception as e:
            print(f"[warn] live pricing unavailable ({e}); using built-in prices", file=sys.stderr)
    lines = []
    for r in spec["resources"]:
        lines.extend(price_resource(r, hours, mult, live))
    total = round(sum(l["monthly_cost"] for l in lines), 2)
    by_cat, by_env, by_svc = defaultdict(float), defaultdict(float), defaultdict(float)
    for l in lines:
        by_cat[l["category"]] += l["monthly_cost"]
        by_env[l["env"]] += l["monthly_cost"]
        by_svc[l["service"]] += l["monthly_cost"]
    rnd = lambda d: {k: round(v, 2) for k, v in sorted(d.items(), key=lambda x: -x[1])}
    return {
        "name": spec.get("name", "estimate"), "region": region, "hours_per_month": hours,
        "region_multiplier": mult, "lines": lines,
        "monthly_total_usd": total, "annual_total_usd": round(total * 12, 2),
        "by_category": rnd(by_cat), "by_env": rnd(by_env), "by_service": rnd(by_svc),
        "currency": spec.get("currency"),
    }


def fmt(v):
    return f"${v:,.2f}"


def print_report(res):
    cur = res.get("currency")
    print(f"# {res['name']}  |  region {res['region']}  |  {res['hours_per_month']} hrs/month\n")
    print("| Category | Service | Resource | Qty | Usage | Unit | Unit price | Monthly | Env | Price src |")
    print("|---|---|---|---:|---:|---|---:|---:|---|---|")
    for l in sorted(res["lines"], key=lambda x: -x["monthly_cost"]):
        print(f"| {l['category']} | {l['service']} | {l['resource']} | {l['qty']} | {l['usage']:,} | "
              f"{l['unit']} | {l['unit_price']} | {fmt(l['monthly_cost'])} | {l['env']} | {l['source']} |")
    print(f"\n**Monthly total: {fmt(res['monthly_total_usd'])}**  |  **Annual: {fmt(res['annual_total_usd'])}**")
    if cur:
        r = cur["rate"]
        print(f"≈ {cur['code']} {res['monthly_total_usd'] * r:,.0f}/month, "
              f"{cur['code']} {res['annual_total_usd'] * r:,.0f}/year (rate {r})")
    print("\n## By category")
    for k, v in res["by_category"].items():
        pct = 100 * v / res["monthly_total_usd"] if res["monthly_total_usd"] else 0
        print(f"- {k}: {fmt(v)} ({pct:.1f}%)")
    if len(res["by_env"]) > 1:
        print("\n## By environment")
        for k, v in res["by_env"].items():
            print(f"- {k}: {fmt(v)}")
    print("\nPrices marked 'approx.' are built-in estimates"
          + (f" scaled by region multiplier {res['region_multiplier']}" if res["region_multiplier"] != 1 else "")
          + ". Excludes tax, support plan, credits and discounts unless listed.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec")
    ap.add_argument("--live", action="store_true", help="optional: EC2/RDS prices from AWS Price List API (needs boto3 + AWS credentials)")
    ap.add_argument("--json", help="write full result JSON to this path")
    a = ap.parse_args()
    with open(a.spec) as f:
        spec = json.load(f)
    res = estimate(spec, a.live)
    print_report(res)
    if a.json:
        with open(a.json, "w") as f:
            json.dump(res, f, indent=2)
        print(f"\nJSON written to {a.json}")


if __name__ == "__main__":
    main()
