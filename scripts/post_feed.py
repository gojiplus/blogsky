#!/usr/bin/env python3
import os
import argparse
import feedparser
import sys
import grapheme
from atproto import Client


def parse_args():
    p = argparse.ArgumentParser(description="Post latest entry from an RSS/Atom feed to Bluesky with link facets")
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
    """Build post text + facets for a feed entry, truncated to 300 graphemes."""
    title = entry.title.strip()
    link = entry.link.strip()
    summary = entry.get("summary", entry.get("description", "")).strip()
    snippet = summary[:200].rsplit(" ", 1)[0] + "…"

    # Build body text (title + snippet) and always append link afterwards
    body_text = f"📝 {title}\n\n{snippet}"
    # Truncate body_text to leave room for link addition
    max_len = 300
    if grapheme.length(body_text) > max_len:
        truncated = grapheme.slice(body_text, 0, max_len)
        if " " in truncated:
            truncated = truncated.rsplit(" ", 1)[0]
        body_text = truncated + "…"

    link_text = link
    # Combine full post
    full_body = f"{body_text}\n\n{link_text}"

    # Compute byte positions for link facet at end
    prefix_bytes = full_body.encode('utf-8')
    # start index is where link_text begins
    link_start = len(body_text.encode('utf-8')) + len("\n\n".encode('utf-8'))
    link_end = link_start + len(link_text.encode('utf-8'))

    facets = [
        {
            "index": {"byteStart": link_start, "byteEnd": link_end},
            "features": [{
                "$type": "app.bsky.richtext.facet#link",
                "uri": link_text
            }]
        }
    ]

    return full_body, facets


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

    entry = entries[0]
    print(f"Posting: {entry.title} -> {entry.link}", file=sys.stderr)
    text, facets = make_post(entry)
    try:
        resp = client.send_post(text, facets=facets)
        print(f"Posted successfully. Response: {resp}", file=sys.stderr)
    except Exception as e:
        print(f"Failed to post: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
