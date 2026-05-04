"""Basic search: find every exposed Elasticsearch in a country."""
import os
from scansearch import Client

api = Client(api_key=os.environ["SCANSEARCH_API_KEY"])

res = api.search("port:9200 country:DE", per_page=50)
print(f"Total: {res.get('total')}")
for hit in res.get("results", [])[:10]:
    print(f"  {hit['ip']:15}  {hit.get('asn_name', '?')}")
