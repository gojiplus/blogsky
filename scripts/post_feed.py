#!/usr/bin/env python3
import os
import argparse
import sys
import feedparser
import grapheme
from atproto import Client


def parse_args():
    p = argparse.ArgumentParser(
        description="Post latest entry from an RSS/Atom feed to Bluesky with link facets"
    )
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

    # Prepare separator and link grapheme counts
    sep = "\n\n"
    link_gr = grapheme.length(link)
    sep_gr = grapheme.length(sep)
    max_total = 300
    # Compute max for body to ensure full <=300
    max_body = max_total - link_gr - sep_gr

    # Initial body
    body = f"📝 {title}\n\n{snippet}"
    # Truncate body to its allowed grapheme length
    if grapheme.length(body) > max_body:
        body = grapheme.slice(body, 0, max_body)
        if " " in body:
            body = body.rsplit(" ", 1)[0]
        body += "…"

    # Combine full post
    full_body = f"{body}{sep}{link}"

    # Byte indices for facet
    b = full_body.encode('utf-8')
    link_start = len(body.encode('utf-8')) + len(sep.encode('utf-8'))
    link_end = link_start + len(link.encode('utf-8'))

    facets = [
        {
            "index": {"byteStart": link_start, "byteEnd": link_end},
            "features": [{
                "$type": "app.bsky.richtext.facet#link",
                "uri": link
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
