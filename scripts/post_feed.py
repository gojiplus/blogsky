import grapheme

def create_post(self, title: str, link: str, abstract: str, authors: str):
    """Create and send a post to Bluesky with correct grapheme handling (full text + link constraint)."""
    prefix = "📄 "

    base_text = f"{prefix}{title} ({authors})"
    
    if abstract:
        base_text += f" {abstract}"

    # Link will be attached separately but link **text** counts toward limit
    # because TextBuilder appends the link inside the post.

    # So we need to simulate final post content now
    link_text = f"\n\n{link}"
    total_post = base_text + link_text

    # Now trim post to <= 300 graphemes
    if grapheme.length(total_post) > 300:
        # We need to trim the base_text so that base_text + link fits
        allowed_base_length = 300 - grapheme.length(link_text)

        base_text = grapheme.slice(base_text, 0, allowed_base_length)

        # Rebuild
        total_post = base_text + link_text

    # Final Safety check
    assert grapheme.length(total_post) <= 300, f"Still too long: {grapheme.length(total_post)} graphemes!"

    # Build the post
    post_builder = client_utils.TextBuilder().text(base_text).text("\n\n").link(link, link)

    try:
        self.client.send_post(post_builder)
        print(f"✅ Posted to Bluesky: {title}")
    except Exception as e:
        print(f"❌ Failed to post '{title}': {e}")
