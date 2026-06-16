# scansearch-python

Official Python SDK and CLI for [**ScanSearch**](https://scansearch.net) — an
**on-demand internet scanner**. Trigger a real SYN + service scan of any IP, CIDR
or country through the REST API and get results in seconds. No stale indexes,
no cached snapshots — actual scans every time.

[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://github.com/ScanSearch/scansearch-python)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## What you can scan

| Target type | Example |
|---|---|
| Single IP | `1.2.3.4` |
| CIDR | `192.0.2.0/24` |
| List of CIDRs / IPs | `["10.0.0.0/8", "203.0.113.5"]` |
| Whole country | country code `DE`, `US`, `CN`, … |
| Domain list | `example.com`, `acme.io` |

## Scan parameters

- **Ports** — any selection: `"22,80,443"`, ranges `"1-65535"`, or full top-list.
- **Modules** — pick what gets collected (see [What gets collected](#what-gets-collected) below).
- **Speed** — your scanner kpps (packets-per-second × 1000), set by your plan.
  Free tier is capped at 2 kpps. Paid plans start at 100 kpps and scale up.
- **Wait or fire-and-forget** — block until done with `scan_wait()`, or poll
  with `scan_status()`.

## What gets collected

Pick which modules run; results are returned per host/port in the scan status response.

### Core (always returned for `ports` + `services` modules)

| Field group | Collects |
|---|---|
| **Service identification** | service name, protocol, banner, software product / vendor / version, CPE, match source, probe used, confidence score |
| **TLS / certificate** | TLS version + cipher, cert issuer / subject / SANs / expiry, SHA-256, age, **JARM** fingerprint, **JA3S** fingerprint |
| **HTTP** | title, server header, status code, full response headers, body hash, favicon hash, redirect chain, robots.txt, security.txt |
| **OS detection** | vendor, family |
| **SSH** | host fingerprint, **HASSH** server fingerprint, host-key type |
| **SMB** | hostname, domain, OS |
| **Reverse DNS** | hostname, rDNS records |
| **DNS records** | MX, NS, TXT, SPF, DMARC, DKIM presence |
| **RDAP / WHOIS** | netname, country, description, abuse email, org, registration date, allocated CIDR |
| **GeoIP / network** | country, city, region, lat/lng, ASN + ASN org, timezone, continent |
| **Threat intelligence** | threat type, threat name, threat score, WAF detection, honeypot score, taxonomy tags |
| **CMS / fingerprinting** | CMS detection, exposed-API flagging |
| **CVE matching** | CVE IDs, CVE count, max CVSS for fingerprinted versions |
| **Certificate Transparency** | CT-derived domain list per cert |
| **Industrial / IoT** | MQTT (auth mode), Modbus (unit ID, device), BACnet (device info) |
| **Cloud** | cloud provider detection |

### Optional modules

| Module | Collects |
|---|---|
| `subdomains` | Subdomain enumeration (subfinder + crt.sh + DNS resolve) for any domain targets in your list. |
| `tech` | Web technology-stack detection (Wappalyzer-style) — CMS, frameworks, JS libs, server software. |

## Pricing

Pay for scan speed only. Linear: **$0.30 per kpps / month**, starting at
**$30/mo for 100 kpps**, scaling up to high-throughput tiers. Free tier
available — no credit card. Crypto checkout supported.

See https://scansearch.net/pricing/ for current details.

## Free vs Paid limits

| | Free | Paid |
|---|---|---|
| Scan speed | 2 kpps | from 100 kpps |
| Targets per scan | 1 country / max 5 ports / max ~1M IPs | Unlimited |
| Scans per day | 3 | Unlimited |
| Concurrent scans | 1 (no queue) | up to 10 in queue |
| Results visible (UI) | First 1 000 | Full result set |
| Download (CSV / TXT) | First 100 rows | Full export |
| API requests | 100 / day | 1 000+ / day, scales with plan |

Free tier is meant for trying the API and one-off small scans. For real recon
you need a paid plan.

## Install

```bash
pip install git+https://github.com/ScanSearch/scansearch-python.git
```

Get an API key: https://scansearch.net/dashboard/api-keys/

```bash
export SCANSEARCH_API_KEY="your-64-char-key"
```

## Quick start (Python)

```python
from scansearch import Client

api = Client()  # picks up SCANSEARCH_API_KEY from env

# 1) Scan a single CIDR for the top web ports, wait until done
job = api.scan(
    targets=["192.0.2.0/24"],
    ports="80,443,8080,8443",
    modules=["ports", "services"],
)
result = api.scan_wait(job["task_id"])
print(f"open ports: {result['open_ports_found']}")
print(f"services:   {result['services_found']}")

# 2) Scan a whole country for one port — fire and forget, poll later
job = api.scan(targets=["country:DE"], ports="9200")
print("task_id:", job["task_id"])
# ... later
print(api.scan_status(job["task_id"]))

# 3) Scan multiple CIDRs at higher speed
job = api.scan(
    targets=["10.0.0.0/16", "192.168.0.0/16"],
    ports="1-1024",
    modules=["ports", "services"],
    speed=1000,  # kpps
)
api.scan_wait(job["task_id"], poll_interval=10)

# 4) Stop a running scan early
api.scan_stop(job["task_id"])
```

## Quick start (CLI)

```bash
# Scan a CIDR for top web ports, block until done, print final result
scansearch scan 192.0.2.0/24 --ports 80,443,8080 --modules ports,services --wait

# Scan a country for a single port at 1000 kpps
scansearch scan country:DE --ports 9200 --speed 1000 --wait

# Poll a running scan
scansearch status 1234

# Stop a running scan
scansearch stop 1234
```

## Use cases

- **Bug-bounty recon** — hit your in-scope CIDRs with a fresh scan and grab
  current open ports + service banners before your competitors do.
- **Asset discovery / shadow IT** — point ScanSearch at your own AS or
  netblocks; find anything exposed that shouldn't be.
- **Vulnerability triage** — combine `services` enrichment with CVE matching
  to find newly exposed instances of `service:ssh`, `service:rdp`, etc.
- **Continuous monitoring** — schedule a daily scan of your CIDRs, diff
  results, alert on new open ports.
- **Country-wide research** — kick off a country scan for a specific service
  (`service:elasticsearch`, `port:9200`) and get a current snapshot.

See [`examples/`](examples/) for runnable scripts.

## Errors

```python
from scansearch import Client, AuthError, RateLimitError, NotFoundError, APIError

try:
    api.scan_status(99999)
except NotFoundError:
    ...
except RateLimitError:
    ...  # daily quota or per-minute rate limit hit
except AuthError:
    ...  # invalid / revoked key
except APIError as e:
    print(e.status, e.body)
```

## Rate limits

Per-account daily and per-minute API limits scale with your plan.
See https://scansearch.net/pricing/ for current limits.

## Development

```bash
git clone https://github.com/ScanSearch/scansearch-python
cd scansearch-python
pip install -e .
```

Pull requests welcome. For non-trivial changes, open an issue first.

## Links

- **Website:** https://scansearch.net
- **API docs:** https://scansearch.net/resources/api-docs/
- **Pricing:** https://scansearch.net/pricing/
- **Free tools** (port scanner, SSL checker, subdomain finder, CVE lookup, …):
  https://scansearch.net/tools/

## License

MIT — see [LICENSE](LICENSE).
