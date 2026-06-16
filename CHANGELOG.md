# Changelog

All notable changes to this project are documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.1.0] - 2026-05-04

### Added
- Initial release of the ScanSearch Python SDK and CLI.
- `scansearch` command-line entry point.
- On-demand SYN + service scans of single IPs, CIDRs, country codes and
  domain lists through the ScanSearch REST API.
- Selectable collection modules (ports, services, TLS / certificate,
  JARM and JA3S fingerprints, and more).
- Blocking (`scan_wait`) and fire-and-forget (`scan_status`) workflows.
- API-key auth via the `SCANSEARCH_API_KEY` environment variable.

[Unreleased]: https://github.com/ScanSearch/scansearch-python/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/ScanSearch/scansearch-python/releases/tag/v0.1.0
