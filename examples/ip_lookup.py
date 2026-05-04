"""Look up a single IP and pretty-print its full record."""
import json
import os
import sys

from scansearch import Client, NotFoundError

api = Client(api_key=os.environ["SCANSEARCH_API_KEY"])

ip = sys.argv[1] if len(sys.argv) > 1 else "1.1.1.1"

try:
    record = api.ip(ip)
    print(json.dumps(record, indent=2))
except NotFoundError:
    print(f"No data for {ip}")
