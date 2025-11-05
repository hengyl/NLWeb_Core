# Copyright (c) 2025 Microsoft Corporation.
# Licensed under the MIT License

"""
RSS/Atom feed parser that converts feeds to schema.org Article format.

Converts RSS/Atom feed entries into schema.org Article objects for
consistent processing in NLWeb.
"""

import feedparser
from typing import List, Dict, Any
from datetime import datetime


async def parse_rss_to_schema(feed_url: str) -> List[Dict[str, Any]]:
    """
    Parse RSS/Atom feed and convert to schema.org Article format.

    Args:
        feed_url: URL or path to RSS/Atom feed

    Returns:
        List of schema.org Article dicts

    Example:
        articles = await parse_rss_to_schema("https://example.com/feed.xml")
    """
    # Parse feed using feedparser
    feed = feedparser.parse(feed_url)

    if not feed.entries:
        print(f"[RSS2SCHEMA] No entries found in feed: {feed_url}")
        return []

    print(f"[RSS2SCHEMA] Parsed {len(feed.entries)} entries from {feed_url}")

    # Convert each entry to schema.org Article
    articles = []
    for entry in feed.entries:
        article = _entry_to_schema_article(entry, feed)
        if article:
            articles.append(article)

    return articles


def _entry_to_schema_article(entry, feed) -> Dict[str, Any]:
    """
    Convert a feed entry to schema.org Article format.

    Args:
        entry: feedparser entry object
        feed: feedparser feed object (for fallback metadata)

    Returns:
        schema.org Article dict
    """
    # Required fields
    url = entry.get('link') or entry.get('id')
    if not url:
        return None

    # Article title
    title = entry.get('title', 'Untitled')

    # Article description/summary
    description = (
        entry.get('summary') or
        entry.get('description') or
        entry.get('content', [{}])[0].get('value', '')
    )

    # Clean HTML from description if present
    if description:
        description = _clean_html(description)

    # Publication date
    date_published = _parse_date(entry.get('published') or entry.get('updated'))

    # Author
    author_name = None
    if entry.get('author'):
        author_name = entry.author
    elif entry.get('author_detail'):
        author_name = entry.author_detail.get('name')

    # Build schema.org Article
    article = {
        '@context': 'http://schema.org',
        '@type': 'Article',
        'url': url,
        'name': title,
        'headline': title,
    }

    # Add optional fields if available
    if description:
        article['description'] = description
        article['articleBody'] = description

    if date_published:
        article['datePublished'] = date_published

    if author_name:
        article['author'] = {
            '@type': 'Person',
            'name': author_name
        }

    # Add publisher info from feed metadata
    if feed.feed.get('title'):
        article['publisher'] = {
            '@type': 'Organization',
            'name': feed.feed.title
        }
        if feed.feed.get('link'):
            article['publisher']['url'] = feed.feed.link

    # Add tags/categories if available
    if entry.get('tags'):
        keywords = [tag.get('term') for tag in entry.tags if tag.get('term')]
        if keywords:
            article['keywords'] = ', '.join(keywords)

    # Add image if available
    if entry.get('media_content'):
        # RSS media:content
        for media in entry.media_content:
            if media.get('medium') == 'image' or 'image' in media.get('type', ''):
                article['image'] = {
                    '@type': 'ImageObject',
                    'url': media['url']
                }
                break
    elif entry.get('enclosures'):
        # RSS enclosures
        for enclosure in entry.enclosures:
            if 'image' in enclosure.get('type', ''):
                article['image'] = {
                    '@type': 'ImageObject',
                    'url': enclosure['url']
                }
                break

    return article


def _clean_html(text: str) -> str:
    """
    Remove HTML tags from text.

    Args:
        text: Text that may contain HTML

    Returns:
        Clean text without HTML tags
    """
    import re

    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)

    # Decode HTML entities
    import html
    text = html.unescape(text)

    # Remove extra whitespace
    text = ' '.join(text.split())

    return text


def _parse_date(date_str: str) -> str:
    """
    Parse date string to ISO format.

    Args:
        date_str: Date string in various formats

    Returns:
        ISO formatted date string (YYYY-MM-DD) or None
    """
    if not date_str:
        return None

    try:
        # feedparser provides time_struct for parsed dates
        if hasattr(date_str, 'timetuple'):
            dt = datetime(*date_str.timetuple()[:6])
            return dt.strftime('%Y-%m-%d')
        return date_str
    except Exception:
        return None
