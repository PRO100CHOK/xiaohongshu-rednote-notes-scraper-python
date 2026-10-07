"""Xiaohongshu (RedNote) scraper — beauty niche trend report + KOL shortlist.

Use case: a cosmetics brand wants to enter China and needs to know what is
trending on Xiaohongshu (小红书) right now and which creators to approach. The
script, with no RedNote login or cookie:

  1. pulls trending notes from the beauty and fashion discovery channels with
     full note details and a profile for every author,
  2. ranks notes by total engagement (likes + saves + comments + shares),
  3. counts the hashtags that repeat across the niche,
  4. builds a creator shortlist in a follower band (micro / mid-tier KOLs),
  5. expands the three hottest hashtags into RedNote's own search suggestions,
  6. saves output.json (all rows) and output.csv (one row per note).

Run:
    pip install -r requirements.txt
    cp .env.example .env
    python main.py

Actor: https://apify.com/pro100chok/rednote-xiaohongshu-scraper?utm_source=github_pro100&utm_medium=readme&utm_campaign=xiaohongshu-rednote-notes-scraper-python
"""
from __future__ import annotations

import csv
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

from apify_client import ApifyClient
from apify_client.errors import ApifyApiError
from dotenv import load_dotenv

ACTOR_ID = "pro100chok/rednote-xiaohongshu-scraper"
CATEGORIES = ["beauty", "fashion"]
MAX_RECORDS = 150                      # notes + author profiles in step 1
KOL_FOLLOWERS = (5_000, 500_000)       # follower band for the shortlist
SUGGESTIONS = 60                       # keyword suggestions in step 2

CSV_FIELDS = [
    "noteId", "sourceCategory", "noteType", "title", "likes", "collects",
    "commentsCount", "shares", "engagementTotal", "hashtags", "ipLocation",
    "publishedAt", "authorName", "authorFollowers", "noteUrl",
]


def run_actor(client: ApifyClient, run_input: dict, label: str) -> list[dict]:
    print(f"-> {label}")
    try:
        run = client.actor(ACTOR_ID).call(run_input=run_input, timeout_secs=1800)
    except ApifyApiError as exc:
        print(f"   failed: {exc}")
        return []
    rows = [r for r in client.dataset(run["defaultDatasetId"]).iterate_items()
            if not r.get("error")]          # error rows are free and carry no data
    print(f"   {len(rows)} rows")
    return rows


def main() -> int:
    load_dotenv()
    token = os.environ.get("APIFY_API_TOKEN")
    if not token:
        sys.exit("APIFY_API_TOKEN missing - copy .env.example to .env and paste your token.")
    client = ApifyClient(token)
    out = Path(__file__).parent

    # Step 1: trending notes + their authors, no login needed
    rows = run_actor(client, {
        "scrapeType": "discoverFeed",
        "feedCategories": CATEGORIES,
        "maxItems": MAX_RECORDS,
        "fullNoteDetail": True,
        "includeAuthorProfile": True,
        "includeVideoStreams": False,
    }, f"discovery feed {CATEGORIES}")
    notes = [r for r in rows if r.get("type") == "note"]
    creators = {r["userId"]: r for r in rows if r.get("type") == "user" and r.get("userId")}
    if not notes:
        sys.exit("No notes returned - try again or pick other categories.")

    # Step 2: rank notes and count hashtags
    notes.sort(key=lambda n: -(n.get("engagementTotal") or 0))
    tags = Counter(t for n in notes for t in (n.get("hashtags") or []))

    print(f"\nTop 10 of {len(notes)} notes by engagement:")
    for n in notes[:10]:
        print(f"  {n.get('engagementTotal') or 0:>7}  [{n.get('sourceCategory')}/"
              f"{n.get('noteType')}]  {(n.get('title') or '')[:40]}  - {n.get('authorName')}")

    print("\nHashtags trending across the niche:")
    for tag, count in tags.most_common(12):
        print(f"  {count:>3}x  #{tag}")

    # Step 3: KOL shortlist in the follower band, scored by engagement per note
    per_author: dict[str, list[int]] = defaultdict(list)
    for n in notes:
        if n.get("authorId"):
            per_author[n["authorId"]].append(n.get("engagementTotal") or 0)
    lo, hi = KOL_FOLLOWERS
    shortlist = []
    for uid, eng in per_author.items():
        c = creators.get(uid)
        if c and lo <= (c.get("followers") or 0) <= hi:
            shortlist.append((sum(eng) / len(eng), c))
    shortlist.sort(key=lambda x: -x[0])

    print(f"\nKOL shortlist ({lo:,}-{hi:,} followers), by engagement per trending note:")
    for avg, c in shortlist[:10]:
        print(f"  {avg:>8.0f}  {c.get('nickname')}  ({c.get('followers'):,} followers, "
              f"{c.get('ipLocation') or '-'}, {c.get('profession') or '-'})  {c.get('profileUrl')}")

    # Step 4: expand the hottest hashtags into RedNote search suggestions
    seeds = [t for t, _ in tags.most_common(3)]
    suggestions = run_actor(client, {
        "scrapeType": "keywordResearch",
        "keywords": seeds,
        "expandKeywords": True,
        "maxItems": SUGGESTIONS,
    }, f"keyword suggestions for {seeds}") if seeds else []
    if suggestions:
        print("\nLong-tail searches RedNote suggests:")
        for s in suggestions[:15]:
            print(f"  {s.get('keyword')} -> {s.get('suggestion')}")

    # Step 5: save
    (out / "output.json").write_text(json.dumps({
        "notes": notes,
        "creators": list(creators.values()),
        "keywordSuggestions": suggestions,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    with (out / "output.csv").open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for n in notes:
            c = creators.get(n.get("authorId")) or {}
            writer.writerow({**n, "hashtags": " ".join(n.get("hashtags") or []),
                             "authorFollowers": c.get("followers")})
    print("\nSaved output.json and output.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
