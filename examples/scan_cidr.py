"""
Launch a live scan of a target and wait for results.

Examples:
    python scan_cidr.py 192.0.2.0/24
    python scan_cidr.py 192.0.2.0/24 22,80,443
    python scan_cidr.py country:DE 9200
"""
import os
import sys

from scansearch import Client

api = Client(api_key=os.environ["SCANSEARCH_API_KEY"])

target = sys.argv[1] if len(sys.argv) > 1 else "192.0.2.0/24"
ports = sys.argv[2] if len(sys.argv) > 2 else "22,80,443,3389,8080"

job = api.scan(targets=[target], ports=ports, modules=["ports", "services"])
print(f"Started scan task {job['task_id']} on {target}")

final = api.scan_wait(job["task_id"], poll_interval=5, timeout=1800)
print(f"  status:         {final.get('status')}")
print(f"  open_ports:     {final.get('open_ports_found')}")
print(f"  services:       {final.get('services_found')}")
print(f"  progress_stage: {final.get('progress_stage')}")
