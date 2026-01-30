import time
import logging
import threading
import signal
import re
import requests

from typing import Any, Dict, Iterable, Optional
from datetime import datetime

from django.db import transaction
from django.conf import settings
from django.core.management.base import BaseCommand

from news.models import Article
from news.providers.newsapiorg.client import NewsApiOrgProvider
from news.providers.newsapiorg.helpers import normalize_articles

from news.services.language_detect.detect import detect_language
from news.services.keyword_extraction.extractor import KeywordExtractorService

logger = logging.getLogger(__name__)

# Configuration constants
TASK_SLEEP_INTERVAL = 5       # Time to wait between batches (seconds)
MAX_RETRIES = 3               # Maximum retries before restarting
BATCH_SIZE = 50               # Number of articles per fetch


class Command(BaseCommand):
    """
    Fetch articles from news provider APIs in a background loop.
    Supports:
    - Graceful shutdown on system signals (SIGTERM, SIGINT, SIGHUP)
    - Multi-threaded fetching for each category if no category is specified
    - Retry logic on transient errors with a maximum retry limit
    - Keyword extraction and language detection for each article
    """
    help = "Fetch articles from provider APIs with proper resource management"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.shutdown_requested = threading.Event()

    # --- Signal Handling ---
    def signal_handler(self, signum, frame):
        self.stdout.write(f"[NEWS] Received signal {signum}, initiating shutdown...")
        self.shutdown_requested.set()

    def setup_signal_handlers(self):
        """Setup graceful shutdown handlers."""
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
        try:
            signal.signal(signal.SIGHUP, self.signal_handler)
        except AttributeError:
            pass  # Not available on Windows

    # --- Sleep ---
    def interruptible_sleep(self, duration: int) -> bool:
        """Sleep that can be interrupted by shutdown signal. Returns True if interrupted."""
        return self.shutdown_requested.wait(duration)

    # --- Arguments ---
    def add_arguments(self, parser):
        parser.add_argument(
            "--interval",
            type=int,
            default=7200,
            help="Sleep interval in seconds between fetch cycles (default (sec): 7200).",
        )
        parser.add_argument(
            "--category",
            type=str,
            default=None,
            help="Optional category to fetch.",
        )
        parser.add_argument(
            "--page-size",
            type=int,
            default=BATCH_SIZE,
            help=f"Number of articles per fetch request (default: {BATCH_SIZE}).",
        )
        parser.add_argument(
            "--country",
            type=str,
            default=None,
            help="Country code for provider requests.",
        )
        parser.add_argument(
            "--once",
            action="store_true",
            help="Run a single fetch cycle and exit.",
        )

    def handle(self, *args, **options):
        self.setup_signal_handlers()
        self.stdout.write("[NEWS] Starting Provider Fetch Task...")
        
        api_key = getattr(settings, 'NEWSAPI_API_KEY', None)
        if not api_key:
            self.stderr.write("[NEWS] Missing NEWSAPI_API_KEY in settings/environment.")
            return
        
        provider = NewsApiOrgProvider(api_key=api_key)
        keyword_extractor = KeywordExtractorService()

        # Check if category is specified
        if not options.get('category'):
            self.stdout.write("[NEWS] No category specified, fetching all supported categories...")
            try:
                supported_categories = provider.categories
                self.stdout.write(f"[NEWS] Found {len(supported_categories)} categories: {', '.join(supported_categories)}")
                
                # Create threads for each category
                threads = []
                for category in supported_categories:
                    category_options = options.copy()
                    category_options['category'] = category
                    thread = threading.Thread(
                        target=self.run_category_fetch,
                        args=(provider, keyword_extractor, category_options, category),
                        name=f"fetch-{category}"
                    )
                    thread.daemon = True
                    thread.start()
                    threads.append(thread)
                    self.stdout.write(f"[NEWS] Started thread for category: {category}")
                
                # Wait for all threads or shutdown signal
                while not self.shutdown_requested.is_set():
                    # Check if any threads are still alive
                    alive_threads = [t for t in threads if t.is_alive()]
                    if not alive_threads:
                        self.stdout.write("[NEWS] All category threads completed")
                        break
                    self.interruptible_sleep(1)
                
                # Wait for threads to finish gracefully
                for thread in threads:
                    thread.join(timeout=5)
                    
            except AttributeError:
                self.stderr.write("[NEWS] Provider does not support categories attribute")
                return
        else:
            # Single category mode (original behavior)
            if options.get('once'):
                self.run_with_retries(provider, keyword_extractor, options)
            else:
                while not self.shutdown_requested.is_set():
                    success = self.run_with_retries(provider, keyword_extractor, options)
                    if not success and not self.shutdown_requested.is_set():
                        self.stdout.write(f"[NEWS] Failed after {MAX_RETRIES} attempts. Restarting...")
                        if self.interruptible_sleep(TASK_SLEEP_INTERVAL):
                            break
                    # Wait for the configured interval before next cycle
                    if self.interruptible_sleep(options.get('interval', 300)):
                        break

        self.stdout.write("[NEWS] Fetch task stopped gracefully")

    def run_category_fetch(self, provider: NewsApiOrgProvider, keyword_extractor: KeywordExtractorService, options: dict, category: str):
        """Run fetch loop for a specific category in a separate thread."""
        self.stdout.write(f"[NEWS][{category}] Starting fetch loop...")
        
        if options.get('once'):
            self.run_with_retries(provider, keyword_extractor, options)
        else:
            while not self.shutdown_requested.is_set():
                success = self.run_with_retries(provider, keyword_extractor, options)
                if not success and not self.shutdown_requested.is_set():
                    self.stdout.write(f"[NEWS][{category}] Failed after {MAX_RETRIES} attempts. Restarting...")
                    if self.interruptible_sleep(TASK_SLEEP_INTERVAL):
                        break
                
                # Wait for the configured interval before next cycle
                if self.interruptible_sleep(options.get('interval', 300)):
                    break
        
        self.stdout.write(f"[NEWS][{category}] Thread stopped")

    def run_with_retries(self, provider: NewsApiOrgProvider, keyword_extractor: KeywordExtractorService, options: dict) -> bool:
        """Try to fetch and process articles with retries."""
        for attempt in range(MAX_RETRIES):
            if self.shutdown_requested.is_set():
                return False

            self.stdout.write(f"[NEWS] Fetch attempt {attempt + 1}/{MAX_RETRIES}")
            if self.interruptible_sleep(TASK_SLEEP_INTERVAL):
                return False

            try:
                self.process_fetch_cycle(provider, keyword_extractor, options)
                return True
            except Exception as e:
                logger.error(f"[NEWS] Critical error: {e}", exc_info=True)
                self.stderr.write(f"[NEWS] Fetch failed: {e}")
                if attempt < MAX_RETRIES - 1:
                    if self.interruptible_sleep(TASK_SLEEP_INTERVAL):
                        return False
        return False

    def process_fetch_cycle(self, provider: NewsApiOrgProvider, keyword_extractor: KeywordExtractorService, options: dict):
        """Single fetch cycle: retrieve and store articles."""
        try:
            articles = provider.get_top_headlines(
                country=options.get('country') or "us",
                category=options.get('category'),
                page_size=options.get('page_size', BATCH_SIZE),
            )
        except requests.exceptions.ConnectionError as e:
            logger.error(f"[NEWS] Network connection error: {e}")
            self.stderr.write("[NEWS] Failed to connect to news API. Check your internet connection.")
            raise
        except requests.exceptions.Timeout as e:
            logger.error(f"[NEWS] Request timeout: {e}")
            self.stderr.write("[NEWS] Request to news API timed out.")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"[NEWS] Request error: {e}")
            self.stderr.write(f"[NEWS] API request failed: {e}")
            raise
        
        self.stdout.write(f"[NEWS] API returned {len(articles)} articles at {datetime.now()}")
        
        if not articles:
            self.stdout.write("[NEWS] No articles retrieved, sleeping...")
            self.interruptible_sleep(options.get('interval', TASK_SLEEP_INTERVAL))
            return

        prepared_articles = []
        for article in normalize_articles(articles):
            if self.shutdown_requested.is_set():
                break

            # Ensure content fields are not None
            title = article.get('title') or ''
            description = article.get('description') or ''
            content = article.get('content') or ''
            
            # combining title, description, content for better keyword extraction
            article_full_content = f"{title} {description} {content}"
            
            # keyword extraction and language detection.
            # fall back to 'en' if detection fails and empty keywords
            keywords, language = self._prepare_article_keywords_and_language(
                article_full_content, keyword_extractor
            )
            if not keywords and not language:
                logger.warning(f"[NEWS] Skipping article due to failed keyword/language extraction: {article.get('url')}")
                continue

            article['keywords'] = keywords
            article['language'] = language
            article['category'] = options.get('category')
            prepared_articles.append(article)

        stored_count = 0
        if prepared_articles:
            # TEMPORARY: Clear existing articles for testing
            # with transaction.atomic():
            #     Article.objects.all().delete()

            # Prepare unique URLs to avoid duplicates in the same batch
            unique_articles = {a["url"]: a for a in prepared_articles}.values()
            urls = [a["url"] for a in unique_articles]

            # Fetch existing articles to avoid duplicates
            existing_urls = set(
                Article.objects.filter(url__in=urls).values_list("url", flat=True)
            )

            # Filter only new articles
            new_articles = [a for a in unique_articles if a["url"] not in existing_urls]

            # Bulk create new articles
            article_objs = [Article(**a) for a in new_articles]
            try:
                with transaction.atomic():
                    Article.objects.bulk_create(article_objs, ignore_conflicts=True)
                stored_count = len(article_objs)
            except Exception as e:
                logger.error(f"[NEWS] Bulk create failed: {e}")

        self.stdout.write(f"[NEWS] Stored {stored_count} new articles")
        self.stdout.write("[NEWS] Waiting before next cycle...")
        self.interruptible_sleep(options.get('interval', TASK_SLEEP_INTERVAL))

    def _prepare_article_keywords_and_language(self, text: str, keyword_extractor: KeywordExtractorService) -> Iterable[Dict[str, Any]]:
        """
        Normalize raw article data from NewsAPI to a standard format.
        Includes keyword extraction and language detection.
        """
        # Extract keywords
        keywords = []
        try:
            # using the keyword extractor service (Yake)
            keywords = keyword_extractor.extract_keywords(text)
            if not keywords:
                return [], 'en'
        except Exception as e:
            logger.warning(f"[NEWS] Keyword extraction failed for {text[:30]}: {e}")
            return [], 'en'
        
        # Detect language using fastText
        language = 'en'
        try:
            # limit text length for detection
            if len(text) > 100:
                text = text[:100]

            lang_result = detect_language(text)
            if lang_result:
                language, confidence = lang_result
        except Exception as e:
            logger.warning(f"[NEWS] Language detection failed for {text[:30]}: {e}")
        
        return keywords, language