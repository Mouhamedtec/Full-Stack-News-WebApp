import logging
import re
from typing import Any, Dict, Iterable

try:
    from django.utils import timezone
except ImportError:
    from .utils import timezone

try:
    from django.utils.dateparse import parse_datetime
except ImportError:
    from .utils import parse_datetime

try:
    from django.core.validators import URLValidator as url_validator
except ImportError:
    from .validators import url_validator

logger = logging.getLogger(__name__)

def normalize_articles(articles: Iterable[Dict[str, Any]]) -> Iterable[Dict[str, Any]]:
    """
    Normalize raw article data from NewsAPI to a standard format.
    Args:
        articles (Iterable[Dict[str, Any]]): Raw articles from NewsAPI.
    Yields:
        Dict[str, Any]: Normalized article data.
    """
    for article in articles:
        title = article.get("title", None)
        url = article.get("url", None)
        content = article.get("content", None)
        description = article.get("description", None)
        source = article.get("source", {}).get("name", None)
        author = article.get("author")
        article_img = article.get("urlToImage", None)
        published_raw = article.get("publishedAt", None)

        # skip articles with missing critical fields
        critical_fields = [title, url, description, source, published_raw]
        if any(v is None for v in critical_fields):
            logger.warning(f"Skipping article due to missing fields")
            continue

        # Get part of description if content is missing
        if not content and description:
            content = description[:200].rstrip() + "..."

        # Skip if content is still None
        if content is None:
            continue

        # Remove NewsAPI truncation pattern like " [+2022 chars]"
        content = re.sub(r'\s+\[\+\d+\s+chars\]', '', content)

        # Parse published date
        try:
            published_date = parse_datetime(published_raw) if published_raw else timezone.now()
        except Exception as e:
            logger.warning(f"Failed to parse date {published_raw}: {e}")
            published_date = timezone.now()

        if not validate_url_and_date({
            "url": url,
            "published_date": published_date
        }):
            continue

        yield {
            "title": title,
            "content": content,
            "description": description,
            "url": url,
            "category": "general",
            "source": source,
            "author": author or source,
            "url_to_image": article_img,
            "published_date": published_date,
            "keywords": [],
            "language": "en",
        }

def validate_url_and_date(article: Dict[str, Any]) -> bool:
    """
    Validate an article's URL and published date.
    Args:
        article (Dict[str, Any]): The article data to validate.
    Returns:
        bool: True if the article is valid, False otherwise.
    """

    url = article.get("url", "")
    published_date = article.get("published_date", None)

    if not url_validator(url):
        logger.warning(f"Invalid URL detected: {url}")
        return False

    if not isinstance(published_date, timezone.datetime):
        logger.warning(f"Invalid published date: {published_date}")
        return False

    return True
