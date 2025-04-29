# BlogSky. Blogspot Atom → Bluesky

**A GitHub Action** to automatically fetch the latest post from a Blogspot Atom/RSS feed and publish it to Bluesky Social every morning.

## Features
- Fetches the newest entry from your Blogspot feed.
- Posts the title and link to Bluesky via the official `atproto` Python client.
- Configurable feed URL, schedule, and post content template.

## Usage
1. Copy this action into your repository under `.github/actions/post-blogspot-to-bsky/`.
2. Add the following workflow in `.github/workflows/post-blogspot.yml`:

```yaml
name: Post Blogspot to Bluesky

on:
  schedule:
    # Every day at 7 AM Pacific Time
    - cron: '0 14 * * *'
  workflow_dispatch:

jobs:
  post:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install feedparser atproto grapheme

      - name: Post latest blogspot entry to Bluesky
        uses: ./github/actions/post-blogspot-to-bsky
        with:
          feed-url: ${{ inputs.feed-url }}
        env:
          BSKY_HANDLE: ${{ secrets.BSKY_HANDLE }}
          BSKY_PASSWORD: ${{ secrets.BSKY_PASSWORD }}
```

## Action Inputs
| Input     | Required | Description                                        |
|-----------|:--------:|----------------------------------------------------|
| `feed-url`|   ✅     | The URL of your Blogspot Atom/RSS feed.            |

## Environment Variables (via `env:`)
- `BSKY_HANDLE` **(required)** — Your Bluesky handle (username).
- `BSKY_PASSWORD` **(required)** — Your Bluesky password.

## How It Works
1. The action fetches the feed specified by `feed-url`.
2. Parses the Atom entries and identifies the newest post.
3. Formats a short message: **title** + link.
4. Logs in to Bluesky and creates a post using the `atproto` client.

## Customization
- **Post template**: Tweak the Python script under `scripts/post_blogspot.py` to change how the content is formatted.
- **Schedule**: Adjust the cron expression under `on.schedule` to post at a different time or frequency.

---

*Built with ❤️ by GojiPlus
