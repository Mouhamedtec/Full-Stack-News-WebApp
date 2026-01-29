# Filtering & Search

This document describes how filtering and search are implemented in the News API endpoint.

## Entry Point
Endpoint: /api/news/ (see base/news/urls.py and base/news/views.py)

The API uses NewsFilterSerializer to validate query parameters and then applies a staged filter pipeline in NewsRetrievalWithFiltersView._apply_filters().

## Filter Pipeline (Order Matters)
1) User language (only when no search is provided)
   - If user_language is set and search is not provided, the queryset is filtered by Article.language (case-insensitive).

2) Language detection from search term
   - If search is provided, language is detected from the search string using services.language_detect.detect_language().
   - If a language is detected, the queryset is filtered by Article.language.

3) User country code -> Source mapping
   - If user_country_code is provided, the Source table is queried for sources in that country.
   - The Article queryset is filtered by source name (Article.source string field) if matching Source names exist.

4) Full-text search + keyword phrase matching
   - Full-text: Q(title__icontains=search) OR Q(content__icontains=search)
   - Keyword phrases: the search string is tokenized into n-grams (up to 4 words) and matched against the JSONField Article.keywords using keywords__icontains.

5) Category, source, author, date range
   - category: Article.category (case-insensitive)
   - source: Article.source (case-insensitive)
   - author: Article.author (case-insensitive contains)
   - date_from/date_to: Article.published_date bounds

## Keyword Phrase Derivation
Implemented in _derive_keyword_phrases():
- Tokenizes on whitespace/punctuation
- Removes surrounding punctuation per token
- Generates n-grams from length N down to 1 (N = min(4, token_count))
- Removes very short grams (< 2 chars)
- Sorts by phrase length (longer/more specific first)
- Caps the number of phrases (max 30 in the API call)

## Sorting
_sort_by supports:
- recent (default): published_date DESC
- oldest: published_date ASC
- title: title ASC

## Response Shape
Results are serialized via ArticleListSerializer, which returns:
- id, title, content_preview, url, category, source, author, url_to_image, published_date

## Notes on Validation
NewsFilterSerializer validates:
- category against VALID_CATEGORIES
- user_language against VALID_LANGUAGES
- user_country_code against VALID_COUNTRIES
