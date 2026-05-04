# scansearch-python

Official Python SDK and CLI for [**ScanSearch**](https://scansearch.net) — a live
internet scanning and exposure-research platform. A fresh-data alternative to
Shodan, Censys and FOFA, with on-demand re-scanning of any target you specify.

[![PyPI](https://img.shields.io/pypi/v/scansearch.svg)](https://pypi.org/project/scansearch/)
[![Python](https://img.shields.io/pypi/pyversions/scansearch.svg)](https://pypi.org/project/scansearch/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## Why ScanSearch

| | ScanSearch | Shodan | Censys |
|---|---|---|---|
| Cheapest paid tier | **$30 / mo** | $69 / mo | $99 / mo |
| Pricing model | Linear, by scan speed | Tiered with feature gates | Tiered with feature gates |
| Live re-scan on demand | **Yes** (seconds) | Limited | Limited |
| Crypto checkout | **Yes** (Coingate) | No | No |
| Free tier | Yes | Limited | Academic only |

The data set covers **370M+ open ports** and **50M+ identified services**
across the global IPv4 space, indexed continuously and refreshed on demand.

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

api = Client()  # reads SCANSEARCH_API_KEY from env

# Find every exposed Elasticsearch in Germany
res = api.search("port:9200 country:DE", per_page=100)
for hit in res["results"]:
    print(hit["ip"], hit.get("ports"), hit.get("asn_name"))

# Look up a single IP
print(api.ip("1.1.1.1"))

# Auto-paginate through all hits for a query (warning: counts against quota)
for hit in api.search_iter("service:elasticsearch country:DE"):
    print(hit["ip"])

# Launch a live scan and wait for results
job = api.scan(targets=["192.0.2.0/24"], ports="22,80,443", modules=["ports", "services"])
final = api.scan_wait(job["task_id"], poll_interval=5)
print(f"Found {final['open_ports_found']} open ports")
```

## Quick start (CLI)

```bash
# Search
scansearch search "port:9200 country:DE" --per-page 50

# IP lookup
scansearch ip 1.1.1.1

# Live scan a CIDR, block until done, print final result
scansearch scan 192.0.2.0/24 --ports 22,80,443 --wait

# Poll a running scan
scansearch status 1234

# Stop a running scan
scansearch stop 1234
```

## Search query syntax

| Pattern | Example | Matches |
|---|---|---|
| Bare IP | `1.2.3.4` | hosts with that exact IP |
| CIDR | `1.2.3.0/24` | hosts within the range |
| `port:N` | `port:9200` | hosts exposing port N |
| `service:S` | `service:http` | hosts running service S |
| `country:CC` | `country:DE` | hosts in country CC |
| `asn:N` | `asn:15169` | hosts in AS N |
| `org:STR` | `org:google` | substring match on AS name |
| free text | `apache 2.4 ubuntu` | full-text on banners / titles / vendor |

Filters can also be passed as kwargs: `api.search("apache", country="DE", port=80)`.

## Use cases

- **Bug bounty recon** — enumerate exposed services on in-scope CIDRs.
- **Asset discovery / shadow IT** — find your own org's misconfigured assets.
- **CVE exposure mapping** — combine `service:` filters with CVE feed data.
- **Continuous monitoring** — schedule daily scans of your CIDRs and diff results.
- **Threat intelligence** — search for known-bad infrastructure patterns.

See [`examples/`](examples/) for full scripts.

## Errors

```python
from scansearch import Client, AuthError, RateLimitError, NotFoundError, APIError

try:
    api.ip("256.0.0.0")
except NotFoundError:
    ...
except RateLimitError:
    # Daily quota or per-minute rate limit hit — back off
    ...
except AuthError:
    # Bad / revoked API key
    ...
except APIError as e:
    print(e.status, e.body)
```

## Rate limits

- **Free tier:** 100 requests/day, 30 req/min per key.
- **Paid plans:** 1000+ req/day, scaling with plan tier.
- **Search results:** up to 100 per page, paginated.

See https://scansearch.net/pricing/ for current limits.

## Development

```bash
git clone https://github.com/scansearch/scansearch-python
cd scansearch-python
pip install -e .
```

Pull requests welcome. For non-trivial changes, open an issue first.

## Links

- **Website:** https://scansearch.net
- **API docs:** https://scansearch.net/resources/api-docs/
- **Pricing:** https://scansearch.net/pricing/
- **Free tools** (port scanner, SSL checker, subdomain finder, etc.):
  https://scansearch.net/tools/
- **Comparison vs Shodan / Censys:** https://scansearch.net/scansearch-vs-shodan-vs-censys/

## License

MIT — see [LICENSE](LICENSE).
