import time
import logging
import threading
import signal
import requests
from django.db import transaction
from datetime import datetime

from django.conf import settings
from django.core.management.base import BaseCommand

from news.providers.newsapiorg.client import NewsApiOrgProvider
from news.models import Source

logger = logging.getLogger(__name__)

# Configuration constants
TASK_SLEEP_INTERVAL = 5
MAX_RETRIES = 3


class Command(BaseCommand):
    """Fetch provider sources repeatedly, mirroring fetch_provider_articles behavior.
    Supports threading for multiple categories, signal handling for graceful shutdown,
    and retry logic on failures.
    """

    help = "Fetch provider sources periodically (supports threading, signals, retries)."

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.shutdown_requested = threading.Event()

    # --- Signal Handling ---
    def signal_handler(self, signum, frame):
        self.stdout.write(f"[NEWS] Received signal {signum}, initiating shutdown...")
        self.shutdown_requested.set()

    def setup_signal_handlers(self):
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
        try:
            signal.signal(signal.SIGHUP, self.signal_handler)
        except AttributeError:
            pass

    # --- Sleep ---
    def interruptible_sleep(self, duration: int) -> bool:
        return self.shutdown_requested.wait(duration)

    def add_arguments(self, parser):
        parser.add_argument(
            "--interval",
            type=int,
            default=21600,
            help="Sleep interval in seconds between fetch cycles (default: 21600, i.e. 6 hours)",
        )
        parser.add_argument("--category", type=str, default=None, help="Optional category to fetch.")
        parser.add_argument("--language", type=str, default=None, help="Filter sources by language")
        parser.add_argument("--country", type=str, default=None, help="Filter sources by country code")
        parser.add_argument("--once", action="store_true", help="Run a single fetch cycle and exit")

    def handle(self, *args, **options):
        self.setup_signal_handlers()
        self.stdout.write("[NEWS] Starting Provider Sources Task...")

        api_key = getattr(settings, "NEWSAPI_API_KEY", None)
        if not api_key:
            self.stderr.write("[NEWS] Missing NEWSAPI_API_KEY in settings/environment.")
            return

        provider = NewsApiOrgProvider(api_key=api_key)

        # Single-cycle mode: run one fetch and exit
        if options.get("once"):
            self.stdout.write("[NEWS] Running single-cycle (once) mode...")
            if not options.get("category"):
                try:
                    supported_categories = provider.categories
                except AttributeError:
                    self.stderr.write("[NEWS] Provider does not support categories attribute")
                    return

                for category in supported_categories:
                    if self.shutdown_requested.is_set():
                        break
                    category_options = options.copy()
                    category_options["category"] = category
                    try:
                        self.process_fetch_cycle(provider, category_options)
                    except Exception as e:
                        logger.error(f"[NEWS] Single-cycle fetch failed for {category}: {e}", exc_info=True)
                        self.stderr.write(f"[NEWS] Single-cycle fetch failed for {category}: {e}")
                return
            else:
                try:
                    self.process_fetch_cycle(provider, options)
                except Exception as e:
                    logger.error(f"[NEWS] Single-cycle fetch failed: {e}", exc_info=True)
                    self.stderr.write(f"[NEWS] Single-cycle fetch failed: {e}")
                return

        # If category not specified, spawn threads per supported category
        if not options.get("category"):
            self.stdout.write("[NEWS] No category specified, fetching all supported categories...")
            try:
                supported_categories = provider.categories
                self.stdout.write(f"[NEWS] Found {len(supported_categories)} categories: {', '.join(supported_categories)}")

                threads = []
                for category in supported_categories:
                    category_options = options.copy()
                    category_options["category"] = category
                    thread = threading.Thread(
                        target=self.run_category_fetch,
                        args=(provider, category_options, category),
                        name=f"sources-{category}",
                    )
                    thread.daemon = True
                    thread.start()
                    threads.append(thread)
                    self.stdout.write(f"[NEWS] Started thread for category: {category}")

                while not self.shutdown_requested.is_set():
                    alive_threads = [t for t in threads if t.is_alive()]
                    if not alive_threads:
                        self.stdout.write("[NEWS] All category threads completed")
                        break
                    self.interruptible_sleep(1)

                for thread in threads:
                    thread.join(timeout=5)

            except AttributeError:
                self.stderr.write("[NEWS] Provider does not support categories attribute")
                return
        else:
            # Single category mode
            while not self.shutdown_requested.is_set():
                success = self.run_with_retries(provider, options)
                if not success and not self.shutdown_requested.is_set():
                    self.stdout.write(f"[NEWS] Failed after {MAX_RETRIES} attempts. Restarting...")
                    if self.interruptible_sleep(TASK_SLEEP_INTERVAL):
                        break

        self.stdout.write("[NEWS] Sources task stopped gracefully")

    def run_category_fetch(self, provider: NewsApiOrgProvider, options: dict, category: str):
        self.stdout.write(f"[NEWS][{category}] Starting sources fetch loop...")
        while not self.shutdown_requested.is_set():
            success = self.run_with_retries(provider, options)
            if not success and not self.shutdown_requested.is_set():
                self.stdout.write(f"[NEWS][{category}] Failed after {MAX_RETRIES} attempts. Restarting...")
                if self.interruptible_sleep(TASK_SLEEP_INTERVAL):
                    break

            if self.interruptible_sleep(options.get("interval", 300)):
                break

        self.stdout.write(f"[NEWS][{category}] Thread stopped")

    def run_with_retries(self, provider: NewsApiOrgProvider, options: dict) -> bool:
        for attempt in range(MAX_RETRIES):
            if self.shutdown_requested.is_set():
                return False

            self.stdout.write(f"[NEWS] Sources fetch attempt {attempt + 1}/{MAX_RETRIES}")
            if self.interruptible_sleep(TASK_SLEEP_INTERVAL):
                return False

            try:
                self.process_fetch_cycle(provider, options)
                return True
            except Exception as e:
                logger.error(f"[NEWS] Critical error while fetching sources: {e}", exc_info=True)
                self.stderr.write(f"[NEWS] Fetch failed: {e}")
                if attempt < MAX_RETRIES - 1:
                    if self.interruptible_sleep(TASK_SLEEP_INTERVAL):
                        return False
        return False

    def process_fetch_cycle(self, provider: NewsApiOrgProvider, options: dict):
        try:
            sources = provider.get_sources(
                language=options.get("language"),
                country=options.get("country"),
                category=options.get("category"),
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

        self.stdout.write(f"[NEWS] API returned {len(sources)} sources at {datetime.now()}")

        if not sources:
            self.stdout.write("[NEWS] No sources retrieved, sleeping...")
            self.interruptible_sleep(TASK_SLEEP_INTERVAL)
            return

        # Persist sources to DB: bulk create new, update existing
        prepared = []
        for _source in sources:
            name = _source.get("name")
            url = _source.get("url")
            cat = _source.get("category")
            lang = _source.get("language")
            country = _source.get("country")

            prepared.append({
                "name": name,
                "url": url,
                "category": cat,
                "language": lang,
                "country": country,
            })

            if prepared:
                names = [p["name"] for p in prepared]
                existing_names = set(Source.objects.filter(name__in=names).values_list("name", flat=True))

                new_items = [Source(**p) for p in prepared if p["name"] not in existing_names]
                updated = 0
                created = 0
                try:
                    with transaction.atomic():
                        if new_items:
                            Source.objects.bulk_create(new_items, ignore_conflicts=True)
                            created = len(new_items)

                        # Update existing records where data changed
                        for p in prepared:
                            if p["name"] in existing_names:
                                try:
                                    obj = Source.objects.get(name=p["name"])
                                    changed = False
                                    for field in ("url", "category", "language", "country"):
                                        if getattr(obj, field) != p[field]:
                                            setattr(obj, field, p[field])
                                            changed = True
                                    if changed:
                                        obj.save()
                                        updated += 1
                                except Source.DoesNotExist:
                                    continue
                except Exception as e:
                    logger.error(f"[NEWS] Failed to persist sources: {e}", exc_info=True)

                # Print summary and items
                self.stdout.write(f"[NEWS] Created {created} new sources, updated {updated} existing sources")

        self.stdout.write("[NEWS] Waiting before next cycle...")
        self.interruptible_sleep(TASK_SLEEP_INTERVAL)

