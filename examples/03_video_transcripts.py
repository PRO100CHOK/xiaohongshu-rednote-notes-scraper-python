"""Download Xiaohongshu video transcripts and MP4 links to local files.

Pulls video notes from the RedNote video channel with full details. Videos
that carry RedNote's auto-generated subtitles get the spoken text attached as
`transcript`; the .srt URLs are always under `videoSubtitles`. Each transcript
is saved to transcripts/<noteId>.txt next to an index of direct video links.

Actor: https://apify.com/pro100chok/rednote-xiaohongshu-scraper?utm_source=github_pro100&utm_medium=readme&utm_campaign=xiaohongshu-rednote-notes-scraper-python
"""
import json
import os
from pathlib import Path

from apify_client import ApifyClient
from dotenv import load_dotenv

load_dotenv()
client = ApifyClient(os.environ["APIFY_API_TOKEN"])

run = client.actor("pro100chok/rednote-xiaohongshu-scraper").call(run_input={
    "scrapeType": "discoverFeed",
    "feedCategories": ["video"],
    "maxItems": 30,
    "fullNoteDetail": True,
    "includeVideoStreams": True,
    "includeTranscripts": True,
})

folder = Path("transcripts")
folder.mkdir(exist_ok=True)
index = []
for n in client.dataset(run["defaultDatasetId"]).iterate_items():
    if n.get("noteType") != "video":
        continue
    index.append({
        "noteId": n.get("noteId"), "title": n.get("title"),
        "durationSec": n.get("videoDuration"), "videoUrl": n.get("videoUrl"),
        "streams": n.get("videoQualityLadder"), "subtitles": n.get("videoSubtitleLanguages"),
        "transcriptLanguage": n.get("transcriptLanguage"), "noteUrl": n.get("noteUrl"),
    })
    if n.get("transcript"):
        (folder / f"{n['noteId']}.txt").write_text(
            f"{n.get('title') or ''}\n{n.get('noteUrl')}\n\n{n['transcript']}", encoding="utf-8")
        print(f"[{n.get('transcriptLanguage')}] {n.get('transcriptCharCount')} chars  {(n.get('title') or '')[:50]}")
    else:
        print(f"[no subtitles]          {(n.get('title') or '')[:50]}")

Path("videos.json").write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\n{len(index)} video notes indexed in videos.json, transcripts in {folder}/")
