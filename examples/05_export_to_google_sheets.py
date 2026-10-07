"""Weekly Xiaohongshu KOL follower tracker in Google Sheets.

Setup:
  1. Google Cloud console -> create a service account -> download its JSON key.
  2. Save it as service_account.json next to this file (it is gitignored).
  3. Share your spreadsheet with the service account's email address.
  4. Put the RedNote creators you work with (or are vetting) in CREATORS.

Each run appends one snapshot row per creator — followers, likes and saves,
region, profession — so the sheet shows how each KOL grows week over week.

Actor: https://apify.com/pro100chok/rednote-xiaohongshu-scraper?utm_source=github_pro100&utm_medium=readme&utm_campaign=xiaohongshu-rednote-notes-scraper-python
"""
import os
from datetime import datetime, timezone

import gspread
from apify_client import ApifyClient
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials

SPREADSHEET = "RedNote KOL tracker"
WORKSHEET = "snapshots"
CREATORS = [
    "https://www.xiaohongshu.com/user/profile/5bbe0958e1e44e00014185bb",
    "https://www.xiaohongshu.com/user/profile/55878481f5a2632c8480b32f",
    "https://www.xiaohongshu.com/user/profile/5ec5e2b0000000000101ef59",
]
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

load_dotenv()
client = ApifyClient(os.environ["APIFY_API_TOKEN"])

run = client.actor("pro100chok/rednote-xiaohongshu-scraper").call(run_input={
    "scrapeType": "userProfiles",
    "userUrls": CREATORS,
    "maxItems": len(CREATORS),
})

stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
rows = []
for u in client.dataset(run["defaultDatasetId"]).iterate_items():
    if u.get("error"):
        print(f"! {u.get('input')}: {u.get('error')}")
        continue
    rows.append([
        stamp, u.get("userId"), u.get("nickname"), u.get("redId"),
        u.get("followers"), u.get("following"), u.get("likesAndCollects"),
        u.get("gender"), u.get("ipLocation"), u.get("profession"),
        ", ".join(u.get("tags") or []), u.get("profileUrl"),
    ])

header = ["date", "user_id", "nickname", "red_id", "followers", "following",
          "likes_and_saves", "gender", "ip_location", "profession", "tags", "profile_url"]
creds = Credentials.from_service_account_file("service_account.json", scopes=SCOPES)
sheet = gspread.authorize(creds).open(SPREADSHEET)
try:
    ws = sheet.worksheet(WORKSHEET)
except gspread.WorksheetNotFound:
    ws = sheet.add_worksheet(WORKSHEET, rows=5000, cols=len(header))
    ws.append_row(header)

ws.append_rows(rows, value_input_option="USER_ENTERED")
print(f"Appended {len(rows)} creator snapshots to {SPREADSHEET}/{WORKSHEET}")
