# Architecture & Technical Details

## High-Level Flow
1) fetch_provider_sources populates Source records from NewsAPI.
2) fetch_provider_articles fetches NewsAPI headlines, normalizes them, extracts keywords, detects language, and stores Article records.
3) /api/news/ exposes filtered, paginated read access to Article records.

## Django Apps
- base: project configuration, settings, URLs
- news: domain app containing models, API views, providers, and services

## Data Model
### Article
- Fields: title, content, description, url, category, source, author, url_to_image, published_date, fetched_date, keywords, language, is_featured, is_archived
- Indexing: multiple compound indexes for query performance (category/language/source + published_date, etc.)
- Uniqueness: (url, source)
- keywords is a JSONField storing keyword-score pairs (e.g., ["term", 0.12])

### Source
- Fields: name, url, category, language, country
- Uniqueness: name
- Indexed fields: country, category+language+country

## Providers
- news/providers/newsapiorg/client.py wraps the NewsAPI client
- normalize_articles() in news/providers/newsapiorg/helpers.py maps NewsAPI output into Article-compatible dicts
- Content sanitization includes removal of NewsAPI truncation markers and URL validation

## Services
### Keyword Extraction
- KeywordExtractorService uses YAKE with a default n-gram size of 3 and returns top 15 keyword-score pairs.
- On failure, it falls back to unique long words from the text.

### Language Detection
See docs/language-detection.md for details.

## REST API
- API view: NewsRetrievalWithFiltersView
- Serializer: ArticleListSerializer (includes content_preview)
- Pagination: DRF PageNumberPagination with default page size 50
- Schema: drf-spectacular at /api/schema/

## Settings Highlights
- Environment: base/.env
- Debug mode uses SQLite; production uses PostgreSQL
- Caching and logging are configured only in non-DEBUG mode

## Files of Interest
- base/news/views.py: filter logic, search, sorting
- base/news/serializers.py: API serializer + filter parameter validation
- base/news/services/language_detect: fastText integration
- base/news/management/commands: background ingestion tasks
