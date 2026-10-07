"""Xiaohongshu comment threads for a list of notes -> quick audience read.

Paste note links exactly as copied from RedNote (share -> copy link); the
xsec_token inside the link is what unlocks the note. xhslink.com short links
are resolved automatically. Replies come back as their own rows, linked to
their parent comment.

Actor: https://apify.com/pro100chok/rednote-xiaohongshu-scraper?utm_source=github_pro100&utm_medium=readme&utm_campaign=xiaohongshu-rednote-notes-scraper-python
"""
import os
from collections import Counter

from apify_client import ApifyClient
from apify_client.errors import ApifyApiError
from dotenv import load_dotenv

NOTE_URLS = [
    "https://www.xiaohongshu.com/explore/6a51b700000000000f028107?xsec_token=ABzPDMicao11A7ioBtbwH1ox1LqAtrhBjv1vTx6xbsXIQ%3D&xsec_source=pc_feed",
]

load_dotenv()
client = ApifyClient(os.environ["APIFY_API_TOKEN"])

try:
    run = client.actor("pro100chok/rednote-xiaohongshu-scraper").call(run_input={
        "scrapeType": "noteComments",
        "noteUrls": NOTE_URLS,
        "maxItems": 300,
        "maxCommentsPerNote": 300,
        "includeSubComments": True,
    })
except ApifyApiError as exc:
    raise SystemExit(f"Run failed: {exc}")

rows = list(client.dataset(run["defaultDatasetId"]).iterate_items())
errors = [r for r in rows if r.get("error")]
comments = [r for r in rows if r.get("type") == "comment" and not r.get("error")]
for e in errors:
    print(f"! {e.get('input')}: {e.get('error')}")

top_level = [c for c in comments if not c.get("isReply")]
print(f"{len(comments)} comments ({len(top_level)} top-level, "
      f"{len(comments) - len(top_level)} replies)\n")

print("Where commenters are (ipLocation):")
for region, n in Counter(c.get("ipLocation") or "-" for c in comments).most_common(8):
    print(f"  {n:>4}  {region}")

creator_replies = sum(1 for c in comments if c.get("isNoteAuthor"))
print(f"\nReplies written by the note's own creator: {creator_replies}")

print("\nMost-liked comments:")
for c in sorted(comments, key=lambda c: -(c.get("likes") or 0))[:10]:
    print(f"  {c.get('likes') or 0:>5}  {(c.get('content') or '')[:90]}")
