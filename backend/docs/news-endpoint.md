# News API Endpoint — NewsRetrievalWithFiltersView

## Endpoint
- **Path:** /api/news/
- **Method:** GET
- **Defined in:** base/base/urls.py and base/news/urls.py

## Purpose
Returns a paginated list of news articles with filtering, full-text search, keyword-phrase matching, sorting, and optional language/country bias.

## Authentication & Throttling
- No explicit permission classes are set on the view, so it is publicly accessible by default.
- Global DRF throttling is enabled in settings:
  - Anon: 1,000,000/day
  - User: 1,000,000/day

## Query Parameters
Validated by `NewsFilterSerializer`.

### Filters
- **search** (string, max 500)
  - Full-text search in title and content.
  - Also derives keyword phrases (n-grams up to 4 words) and matches against `Article.keywords` JSONField.
  - If provided, language is auto-detected and used to filter results.

- **category** (string)
  - Must be one of: business, entertainment, general, health, science, sports, technology.

- **source** (string)
  - Case-insensitive exact match on `Article.source`.

- **author** (string)
  - Case-insensitive contains match on `Article.author`.

- **user_language** (string)
  - Used only if `search` is not provided.
  - Must be one of `VALID_LANGUAGES`.

- **user_country_code** (string)
  - Maps to `Source.country`, then filters `Article.source` by matching `Source.name`.
  - Must be one of `VALID_COUNTRIES`.

- **date_from** (ISO 8601 datetime)
  - Filters `published_date >= date_from`.

- **date_to** (ISO 8601 datetime)
  - Filters `published_date <= date_to`.

### Sorting
- **sort_by** (choice: recent | oldest | title)
  - recent (default): published_date DESC
  - oldest: published_date ASC
  - title: title ASC

### Pagination
- Uses DRF `PageNumberPagination` with default page size 50.
- Supports `page` query param.
- `page_size` is not enabled unless the paginator is customized.

## Filter Pipeline (Order)
1) **user_language** (only when `search` is absent)
2) **Language detection from search**
3) **user_country_code → Source mapping**
4) **Full-text search + keyword phrase matching**
5) **category, source, author, date range**

## Keyword Phrase Matching (Search Behavior)
- Tokenizes the search text.
- Generates n-grams up to 4 words (max 30 phrases).
- Matches against `Article.keywords` JSONField using case-insensitive substring search.

## Response (200 OK)
Paginated response (standard DRF):
- **count** (int)
- **next** (url or null)
- **previous** (url or null)
- **results** (array of articles)

Each article includes:
- **id**
- **title**
- **content_preview** (first 200 chars of content)
- **url**
- **category**
- **source**
- **author**
- **url_to_image**
- **published_date**

## Error Responses
- **400 Bad Request**: invalid query params (serializer errors)
- **500 Internal Server Error**: unexpected server errors

## Example Request
- `/api/news/?search=climate%20policy&category=science&sort_by=recent&page=1`

## OpenAPI
- **Schema:** /api/schema/
- **Swagger UI:** /api/schema/swagger-ui/
