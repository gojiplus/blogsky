#!/usr/bin/env python3
import os
import argparse
import feedparser
import sys
from atproto import Client, client_utils

def parse_args():
    p = argparse.ArgumentParser(description="Post latest entry from an RSS/Atom feed to Bluesky")
    p.add_argument(
        "--feed-url", required=True,
        help="RSS/Atom feed URL (e.g. Blogspot Atom feed)"
    )
    return p.parse_args()


def load_feed(url):
    """Fetch and return feed entries."""
    parsed = feedparser.parse(url)
    if parsed.bozo:
        print(f"Error parsing feed: {parsed.bozo_exception}", file=sys.stderr)
        return []
    return parsed.entries


def make_post(entry):
    """Build a Bluesky post for a feed entry."""
    title = entry.title.strip()
    link = entry.link.strip()
    summary = entry.get("summary", entry.get("description", "")).strip()
    # trim summary to ~200 chars at word boundary
    snippet = summary[:200].rsplit(" ", 1)[0] + "…"
    text = f"📝 {title}\n\n{snippet}"
    return client_utils.TextBuilder()\
        .text(text)\
        .text("\n\n")\
        .link(link, link)


def main():
    args = parse_args()
    handle = os.getenv("BSKY_HANDLE")
    pwd = os.getenv("BSKY_PASSWORD")
    if not handle or not pwd:
        print("ERROR: BSKY_HANDLE and BSKY_PASSWORD must be set", file=sys.stderr)
        sys.exit(1)

    client = Client()
    session = client.login(handle, pwd)
    print(f"Logged in as: {getattr(session, 'handle', handle)}", file=sys.stderr)

    entries = load_feed(args.feed_url)
    if not entries:
        print("No entries found in feed.", file=sys.stderr)
        return

    # Post only the newest item
    entry = entries[0]
    print(f"Posting: {entry.title} -> {entry.link}", file=sys.stderr)
    post = make_post(entry)
    try:
        resp = client.send_post(post)
        print(f"Posted successfully. Response: {resp}", file=sys.stderr)
    except Exception as e:
        print(f"Failed to post: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
