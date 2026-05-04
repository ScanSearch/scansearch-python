"""
Continuous monitoring example — scan a CIDR, diff against the previous run,
print newly opened or closed ports.

  python monitor_diff.py 192.0.2.0/24

Saves last results to ./scansearch_state.json. Run on a cron / systemd timer.
"""
import json
import os
import sys
from pathlib import Path

from scansearch import Client

STATE_FILE = Path("scansearch_state.json")
api = Client(api_key=os.environ["SCANSEARCH_API_KEY"])

target = sys.argv[1] if len(sys.argv) > 1 else "192.0.2.0/24"
ports = sys.argv[2] if len(sys.argv) > 2 else "1-1024"

job = api.scan(targets=[target], ports=ports, modules=["ports"])
final = api.scan_wait(job["task_id"], poll_interval=10)

# Pull current open IP:port set from the scan result.
# (Adjust to match the exact response shape you receive from /scan/<id>/status/.)
current = set()
for host in final.get("hosts") or []:
    ip = host.get("ip")
    for port in host.get("open_ports") or []:
        current.add(f"{ip}:{port}")

previous = set()
if STATE_FILE.exists():
    previous = set(json.loads(STATE_FILE.read_text()))

newly_opened = current - previous
newly_closed = previous - current

print(f"Target {target}: {len(current)} open ports total")
if newly_opened:
    print(f"  +{len(newly_opened)} newly opened:")
    for x in sorted(newly_opened):
        print(f"    {x}")
if newly_closed:
    print(f"  -{len(newly_closed)} newly closed:")
    for x in sorted(newly_closed):
        print(f"    {x}")
if not newly_opened and not newly_closed:
    print("  no changes since last run")

STATE_FILE.write_text(json.dumps(sorted(current)))
