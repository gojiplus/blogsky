#!/usr/bin/env python3
import os
import argparse
import sys
import re
import html
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
    """Build post text + facets, truncate to 300 graphemes, strip HTML/entities and use 'link' facet."""
    # Clean HTML and entities from title
    raw_title = html.unescape(re.sub(r'<[^>]+>', '', entry.title))
    title = raw_title.replace('\u00a0', ' ').strip()
    link = entry.link.strip()

    # Clean HTML and entities from summary/description
    raw_summary = entry.get("summary", entry.get("description", ""))
    summary_text = html.unescape(re.sub(r'<[^>]+>', '', raw_summary))
    summary = summary_text.replace('\u00a0', ' ').strip()
    snippet = summary[:200].rsplit(" ", 1)[0] + "…"

    # Prepare separators
    sep = "\n\n"
    link_text = "link"

    # Compute grapheme length allowances
    link_gr = grapheme.length(link_text)
    sep_gr = grapheme.length(sep)
    max_total = 300
    max_body = max_total - link_gr - sep_gr

    # Build body and truncate safely
    body = f"📝 {title}{sep}{snippet}"
    if grapheme.length(body) > max_body:
        body = grapheme.slice(body, 0, max_body)
        # back off to last word boundary
        if " " in body:
            body = body.rsplit(" ", 1)[0]
        body += "…"

    # Full post
    full_body = f"{body}{sep}{link_text}"

    # Byte indices for facet
    b = full_body.encode('utf-8')
    body_bytes = body.encode('utf-8') + sep.encode('utf-8')
    link_start = len(body_bytes)
    link_end = link_start + len(link_text.encode('utf-8'))

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

