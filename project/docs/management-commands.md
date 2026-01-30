# Management Commands

Two custom management commands are provided in base/news/management/commands.

## fetch_provider_articles
Purpose: pull top headlines from NewsAPI, extract keywords, detect language, and store new articles.

### Command
python manage.py fetch_provider_articles [options]

### Options
- --interval: sleep interval between cycles (seconds). Default: 7200
- --category: optional NewsAPI category
- --page-size: number of articles per fetch. Default: 50
- --country: country code for NewsAPI
- --once: run a single cycle and exit

### Behavior
- If --category is omitted, the command spawns a thread per provider category.
- Each thread performs fetch/retry cycles until shutdown is requested.
- Retries are capped at MAX_RETRIES (3). Between retries, it sleeps TASK_SLEEP_INTERVAL (5 seconds).
- Signals SIGTERM/SIGINT (and SIGHUP where available) trigger a clean shutdown.

### Article Processing
- Uses normalize_articles() to map NewsAPI fields to the Article model fields.
- Builds a full text by combining title + description + content.
- Extracts keywords using YAKE (KeywordExtractorService).
  - If keyword extraction fails, it falls back to extracting long unique words.
- Detects language via fastText on a truncated snippet (first 100 chars).
- Uses bulk_create for new articles, skipping URLs that already exist.

## fetch_provider_sources
Purpose: pull source metadata from NewsAPI and upsert Source records.

### Command
python manage.py fetch_provider_sources [options]

### Options
- --interval: sleep interval between cycles (seconds). Default: 21600
- --category: optional category
- --language: filter sources by language
- --country: filter sources by country
- --once: run a single cycle and exit

### Behavior
- If --category is omitted, the command spawns a thread per provider category.
- Retries are capped at MAX_RETRIES (3) with TASK_SLEEP_INTERVAL (5 seconds) between attempts.
- Sources are bulk-created when new and updated in-place if fields change.

## Required Settings
Both commands expect NEWSAPI_API_KEY to be present in settings (from .env).
