"""A creator's recent RedNote posts -> CSV, with pandas stats per creator.

`userNotes` returns each creator's profile row plus their recent notes. Here we
keep the notes, compute posting cadence and median likes per creator, and save
an Excel-friendly CSV (UTF-8 with BOM so Chinese text displays correctly).

Actor: https://apify.com/pro100chok/rednote-xiaohongshu-scraper?utm_source=github_pro100&utm_medium=readme&utm_campaign=xiaohongshu-rednote-notes-scraper-python
"""
import os

import pandas as pd
from apify_client import ApifyClient
from dotenv import load_dotenv

CREATORS = [
    "https://www.xiaohongshu.com/user/profile/5ec5e2b0000000000101ef59",
    "https://www.xiaohongshu.com/user/profile/55878481f5a2632c8480b32f",
]

load_dotenv()
client = ApifyClient(os.environ["APIFY_API_TOKEN"])

run = client.actor("pro100chok/rednote-xiaohongshu-scraper").call(run_input={
    "scrapeType": "userNotes",
    "userUrls": CREATORS,
    "maxNotesPerUser": 30,
    "maxItems": 100,
    "fullNoteDetail": False,     # listing cards only: faster, enough for stats
})

df = pd.DataFrame(client.dataset(run["defaultDatasetId"]).iterate_items())
if df.empty or "type" not in df.columns:
    raise SystemExit("Nothing returned.")
notes = df[df["type"] == "note"].copy()

cols = [c for c in ["authorName", "publishedAt", "noteType", "title", "likes",
                    "pinned", "noteUrl"] if c in notes.columns]
notes = notes[cols]
if "publishedAt" in notes.columns:
    notes["publishedAt"] = pd.to_datetime(notes["publishedAt"], errors="coerce", utc=True)
    notes = notes.sort_values(["authorName", "publishedAt"], ascending=[True, False])

summary = notes.groupby("authorName").agg(
    posts=("title", "size"),
    median_likes=("likes", "median"),
    video_share=("noteType", lambda s: round((s == "video").mean(), 2)),
)
print(summary.to_string())

notes.to_csv("output.csv", index=False, encoding="utf-8-sig")
print(f"\nSaved {len(notes)} notes to output.csv")
