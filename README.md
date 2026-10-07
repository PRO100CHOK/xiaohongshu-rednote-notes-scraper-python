# Xiaohongshu (RedNote) Notes Scraper — Python Example (小红书 爬虫)

> Scrape Xiaohongshu / RedNote notes, images, video links, subtitles and transcripts, creator profiles, comment threads and keyword suggestions from Python — six of eight modes need no login, no cookie and no QR scan.

[![Apify Actor](https://img.shields.io/badge/Apify-Actor-red)](https://apify.com/pro100chok/rednote-xiaohongshu-scraper?utm_source=github_pro100&utm_medium=readme&utm_campaign=xiaohongshu-rednote-notes-scraper-python)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-green)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

A working Python project built on the [RedNote Xiaohongshu Scraper API on Apify](https://apify.com/pro100chok/rednote-xiaohongshu-scraper?utm_source=github_pro100&utm_medium=readme&utm_campaign=xiaohongshu-rednote-notes-scraper-python). It turns 小红书 (XHS, Little Red Book) into a flat, sortable dataset: notes with parsed engagement numbers, direct MP4 links, `.srt` subtitle tracks and spoken-text transcripts, creators with followers and 小红书号, and comments with replies linked to their parents.

## What this does

Xiaohongshu is where Chinese consumers research before they buy — skincare routines, restaurant picks, travel itineraries, outfit ideas. For brands, agencies and researchers outside China, it is also one of the hardest platforms to get data out of. There is no public content API for third parties, the web app signs every request, and most existing scrapers ask you to export your own session cookie (which puts that account at risk).

The actor behind this repo takes a different route: it opens its own anonymous guest session and uses plain HTTP requests — no headless browser — so feeds, note details, comments, creator profiles, creator posts and keyword research all work **without any RedNote account**. Only the two keyword-search modes need a cookie, because RedNote answers search only for signed-in users.

Every record streams into the dataset as soon as it is parsed, so stopping a run early still leaves you with everything collected so far. Inputs that cannot be opened come back as an explanatory `error` row that is never charged.

## Use cases

- **China market entry research** — what is trending in beauty, food, fashion, travel or fitness this week, measured by real likes, saves and shares.
- **KOL / influencer vetting** — followers, likes and saves, region, profession and profile tags for a list of creators, plus their recent posts.
- **Influencer discovery** — pull trending notes in a channel with `includeAuthorProfile` and get a profile row for every author.
- **Comment and sentiment analysis** — full comment threads with likes, region (`ipLocation`) and a flag for replies written by the creator.
- **Video repurposing and AI datasets** — direct video links, every stream rendition and the transcript of RedNote's auto-generated subtitles.
- **Xiaohongshu SEO and content planning** — RedNote's own search suggestions for any Chinese or English seed, expanded recursively into a long-tail map.
- **Competitive monitoring** — re-scrape a fixed list of note URLs to track how a competitor's posts gain engagement over time.

## Requirements

- Python **3.10+**
- A free [Apify account](https://console.apify.com/sign-up) — the free plan includes $5 of monthly credits (roughly 1,000 fully detailed notes)
- **No** RedNote account or cookie for six of the eight modes

## Quick start

```bash
git clone https://github.com/pro100chok/xiaohongshu-rednote-notes-scraper-python.git
cd xiaohongshu-rednote-notes-scraper-python
pip install -r requirements.txt
cp .env.example .env
# paste your APIFY_API_TOKEN into .env
python main.py
```

`main.py` produces a **beauty-niche trend report and KOL shortlist**: it collects trending notes from the beauty and fashion channels with full details and author profiles, ranks notes by `engagementTotal`, counts recurring hashtags, shortlists creators between 5,000 and 500,000 followers by engagement per trending note, expands the three hottest hashtags into RedNote search suggestions, and writes `output.json` and `output.csv`.

The smallest possible call:

```python
from apify_client import ApifyClient

client = ApifyClient("YOUR_APIFY_TOKEN")
run = client.actor("pro100chok/rednote-xiaohongshu-scraper").call(run_input={
    "scrapeType": "discoverFeed",
    "feedCategories": ["food", "travel"],
    "maxItems": 50,
})
for note in client.dataset(run["defaultDatasetId"]).iterate_items():
    print(note.get("title"), note.get("likes"), note.get("noteUrl"))
```

## The eight modes

| `scrapeType` | Input field | Returns | Login |
|---|---|---|---|
| `discoverFeed` | `feedCategories` | Trending notes from 12 channels: recommended, fashion, food, beauty, movies, career, relationships, home, gaming, travel, fitness, video | No |
| `noteDetails` | `noteUrls` | Full payload of specific notes | No |
| `noteComments` | `noteUrls` | Comments and replies as separate linked rows | No |
| `userProfiles` | `userUrls` | Creator profile stats | No |
| `userNotes` | `userUrls` | A creator's profile plus recent posts | No |
| `keywordResearch` | `keywords` | RedNote search suggestions | No |
| `searchNotes` | `keywords` + `cookie` | Keyword search over notes with sort, post-type and date filters | Cookie |
| `searchUsers` | `keywords` + `cookie` | Keyword search over creators | Cookie |

If the field your mode reads is empty but another one is filled in, the run switches to the mode that matches your input and says so in the log, instead of finishing with nothing.

**Note links:** paste them exactly as RedNote's share button copies them. The `xsec_token` parameter in the link is the access key for that note. `xhslink.com` short links are resolved automatically, and every output row hands the token back as `xsecToken` so you can chain modes later.

## Example output

A note with full detail (trimmed):

```json
{
  "type": "note",
  "noteId": "6453436d000000000800c87b",
  "noteType": "image",
  "title": "芭蕾舞女孩蛋糕 六寸蛋糕 女生蛋糕",
  "likes": 23,
  "collects": 15,
  "commentsCount": 4,
  "shares": 4,
  "engagementTotal": 46,
  "likesText": "23",
  "publishedAt": "2023-05-04T05:32:29Z",
  "ipLocation": "河南",
  "authorName": "宸一烘焙~（👀简介）",
  "hashtags": ["蛋糕", "最好吃的奶油蛋糕", "生日蛋糕"],
  "imageCount": 9,
  "coverUrlOriginal": "https://sns-img-qc.xhscdn.com/1000g0082pam93cgjq0205n106eg1oa8j4dto510",
  "sourceCategory": "food"
}
```

Video notes add `videoUrl`, `videoBackupUrls`, `videoStreams` (codec, resolution, bitrate per rendition), `videoDuration`, `videoFps`, `videoSubtitles` and, with transcripts on, `transcript`, `transcriptLanguage` and `transcriptCharCount`. Counters come both as RedNote prints them (`likesText: "10万+"`) and as integers (`likes: 100000`). Image rows include non-expiring original links (`imageUrlsOriginal`) next to RedNote's signed, time-limited ones.

Creator rows carry `nickname`, `redId`, `followers`, `following`, `likesAndCollects`, `gender`, `ipLocation`, `profession`, `tags` and `profileUrl`. Comment rows carry `content`, `likes`, `replyCount`, `isReply`, `parentCommentId`, `isNoteAuthor`, `ipLocation` and `createdAt`.

## Input parameters

| Field | Type | What it does |
|---|---|---|
| `scrapeType` | enum | One of the eight modes (default `discoverFeed`) |
| `feedCategories` | array | Discovery channels; results are split evenly between them |
| `noteUrls` | array | Note links, share links or bare note IDs |
| `userUrls` | array | Profile links or bare user IDs |
| `keywords` | array | Seeds for keyword research and search |
| `maxItems` | int | Hard cap on records pushed (default 100) |
| `fullNoteDetail` | bool | Open every note for body, all images, video streams, hashtags and region (default on) |
| `includeComments`, `includeSubComments` | bool | Add comments (and replies) to any note mode |
| `maxCommentsPerNote`, `maxNotesPerUser` | int | Per-note and per-creator limits |
| `includeAuthorProfile` | bool | Add a full profile row for each distinct author |
| `includeVideoStreams`, `includeTranscripts` | bool | Every video rendition; spoken-text transcripts |
| `expandKeywords` | bool | Feed suggestions back in as new seeds |
| `searchSortBy`, `searchNoteType`, `searchTimeFilter` | enum | Filters for the cookie-based search modes |
| `cookie` | string (secret) | Only for `searchNotes` / `searchUsers` |
| `includeRawData` | bool | Attach the untouched RedNote payload under `raw` |

## More examples

| File | What it shows |
|---|---|
| [`examples/01_basic_usage.py`](examples/01_basic_usage.py) | 20 trending food notes with likes, saves and links |
| [`examples/02_comments_analysis.py`](examples/02_comments_analysis.py) | Comment threads for note URLs: regions, creator replies, most-liked comments |
| [`examples/03_video_transcripts.py`](examples/03_video_transcripts.py) | Video notes with transcripts saved to text files and an index of MP4 links |
| [`examples/04_export_to_csv.py`](examples/04_export_to_csv.py) | Creators' recent posts to CSV with posting stats per creator in pandas |
| [`examples/05_export_to_google_sheets.py`](examples/05_export_to_google_sheets.py) | Weekly KOL follower snapshots appended to a Google Sheet |

## How much does it cost?

Pay per result, proxies included. On the free plan: **$5.00 per 1,000 notes**, $2.00 per 1,000 comments, $10.00 per 1,000 creator profiles and $1.00 per 1,000 keyword suggestions. Higher Apify plans pay less automatically, down to $3.50 per 1,000 notes. Error rows are never charged.

## FAQ

**Does Xiaohongshu have an official API?**
Not for content. RedNote's open platform covers business and advertising integrations; it does not hand third parties notes, creators or comments. The [RedNote scraper](https://apify.com/pro100chok/rednote-xiaohongshu-scraper?utm_source=github_pro100&utm_medium=readme&utm_campaign=xiaohongshu-rednote-notes-scraper-python) fills that gap.

**Do I need to log in or share my cookie?**
Only for `searchNotes` and `searchUsers`. Feeds, note details, comments, profiles, creator notes and keyword research run on an anonymous session the actor creates itself.

**Why does a bare note ID sometimes fail?**
RedNote needs the `xsec_token` that comes with the shared link. Paste the full link, or reuse the `xsecToken` returned by an earlier run.

**Can I download Xiaohongshu videos?**
Every video note includes a direct `videoUrl` plus backup mirrors and, with `includeVideoStreams`, every rendition RedNote exposes.

**Can I get transcripts of RedNote videos?**
Yes, for videos that carry RedNote's auto-generated subtitles. Turn on `includeTranscripts`; the subtitle `.srt` URLs are returned either way.

**Why does `fullNoteDetail` matter?**
With it off, only the listing card (title, cover, author, likes, date) is kept — several times faster. Leave it on when you need captions, hashtags, all images or video data.

## Related actors

- [TikTok Profile Scraper](https://apify.com/pro100chok/tiktok-profile-pro?utm_source=github_pro100&utm_medium=readme&utm_campaign=xiaohongshu-rednote-notes-scraper-python) — creator profiles, contacts and leads
- [Instagram Scraper](https://apify.com/pro100chok/instagram-scraper-all-in-one?utm_source=github_pro100&utm_medium=readme&utm_campaign=xiaohongshu-rednote-notes-scraper-python) — profiles, posts, reels and comments
- [Naver Scraper](https://apify.com/pro100chok/naver-all-in-one-scraper?utm_source=github_pro100&utm_medium=readme&utm_campaign=xiaohongshu-rednote-notes-scraper-python) — Korea's Map, Shopping, Blog, Cafe and News
- [TikTok Shop Scraper](https://apify.com/pro100chok/tiktok-shop-scraper-usage?utm_source=github_pro100&utm_medium=readme&utm_campaign=xiaohongshu-rednote-notes-scraper-python) — products, sales and reviews
- [YouTube Scraper](https://apify.com/pro100chok/youtube-scraper-all-in-one?utm_source=github_pro100&utm_medium=readme&utm_campaign=xiaohongshu-rednote-notes-scraper-python) — videos, shorts and comments

## License

MIT — see [LICENSE](LICENSE). Not affiliated with or endorsed by Xiaohongshu / RedNote. Collect only public data and handle personal data such as nicknames and comments in line with PIPL, GDPR and other laws that apply to you.

---

Built by [pro100chok](https://apify.com/pro100chok/rednote-xiaohongshu-scraper?utm_source=github_pro100&utm_medium=readme&utm_campaign=xiaohongshu-rednote-notes-scraper-python) on Apify.
