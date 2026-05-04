# scansearch-python

Official Python SDK and CLI for [**ScanSearch**](https://scansearch.net) — an
**on-demand internet scanner**. Trigger a real SYN + service scan of any IP, CIDR
or country through the REST API and get results in seconds. No stale indexes,
no cached snapshots — actual scans every time.

[![PyPI](https://img.shields.io/pypi/v/scansearch.svg)](https://pypi.org/project/scansearch/)
[![Python](https://img.shields.io/pypi/pyversions/scansearch.svg)](https://pypi.org/project/scansearch/)
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
- **Modules** — pick what gets collected:
  - `ports` — open-port discovery only (fastest).
  - `ports`, `services` — port + service/banner detection.
  - extra enrichment available: subdomains, screenshots, technology stack, security headers, CVE matching.
- **Speed** — your scanner kpps (packets-per-second × 1000), set on your plan:
  - Free tier: capped at `2` kpps.
  - Paid: from `100` kpps (entry) up to `10000` kpps (high-throughput recon).
- **Wait or fire-and-forget** — block until done with `scan_wait()`, or poll
  with `scan_status()`.

## Install

```bash
pip install scansearch
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
