"""20 trending Xiaohongshu food notes — no login, no cookie.

Actor: https://apify.com/pro100chok/rednote-xiaohongshu-scraper?utm_source=github_pro100&utm_medium=readme&utm_campaign=xiaohongshu-rednote-notes-scraper-python
"""
import os

from apify_client import ApifyClient
from dotenv import load_dotenv

load_dotenv()
client = ApifyClient(os.environ["APIFY_API_TOKEN"])

run = client.actor("pro100chok/rednote-xiaohongshu-scraper").call(run_input={
    "scrapeType": "discoverFeed",
    "feedCategories": ["food"],
    "maxItems": 20,
})

for n in client.dataset(run["defaultDatasetId"]).iterate_items():
    print(f"{n.get('likes') or 0:>7} likes  {n.get('collects') or 0:>6} saves  "
          f"{(n.get('title') or '')[:40]:<40}  {n.get('authorName')}  {n.get('noteUrl')}")
