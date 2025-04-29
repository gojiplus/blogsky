#!/usr/bin/env python3
import os
import argparse
import feedparser
from atproto import Client, client_utils

def parse_args():
    p = argparse.ArgumentParser(description="Post RSS/Atom feed items to Bluesky")
    p.add_argument(
        "--feed-url",
        required=True,
        help="RSS/Atom feed URL (e.g. Blogspot, Medium, etc.)"
    )
    return p.parse_args()

def load_feed(url):
    return feedparser.parse(url).entries

def already_seen():
    # simple in-memory set; persists only for the run
    return set()

def mark_seen(seen, entry_id):
    seen.add(entry_id)

def make_post(entry):
    title = entry.title
    link  = entry.link
    snippet = (entry.summary or entry.get("description",""))[:200].rsplit(" ",1)[0] + "…"
    text = f"📝 {title}\n\n{snippet}"
    return client_utils.TextBuilder().text(text).text("\n\n").link(link, link)

def main():
    args = parse_args()
    client = Client(); client.login(os.getenv("BSKY_HANDLE"), os.getenv("BSKY_PASSWORD"))

    seen = already_seen()
    for entry in load_feed(args.feed_url):
        uid = entry.get("id", entry.link)
        if uid in seen:
            continue
        post = make_post(entry)
        client.send_post(post)
        mark_seen(seen, uid)

if __name__=="__main__":
    main()
