from typing import List
import asyncio
import time
import httpx
import logging

from .config import settings
from .cache import DatasetStore
from .models import Message

log = logging.getLogger(__name__)


class MessagesClient:
    def __init__(self, dataset: DatasetStore):
        self.base_url = settings.upstream_api_url.rstrip("/")
        self.timeout = settings.upstream_timeout_seconds
        self._lock = asyncio.Lock()
        self.dataset = dataset

    async def fetch_all_messages(self, force: bool = False) -> List[Message]:
        """Fetch all messages and populate the dataset."""
        if not force and self.dataset.is_fresh(settings.cache_ttl_seconds):
            log.info("Dataset is fresh, using cached data")
            return self.dataset.messages

        async with self._lock:
            if not force and self.dataset.is_fresh(settings.cache_ttl_seconds):
                return self.dataset.messages

            log.info("Fetching messages from upstream API...")
            messages: List[Message] = []
            skip = 0
            limit = settings.bootstrap_limit
            pages_fetched = 0
            hit_rate_limit = False

            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                while True:
                    retry_count = 0
                    max_retries = 10
                    page_success = False

                    while retry_count <= max_retries and not page_success:
                        try:
                            resp = await client.get(
                                f"{self.base_url}/messages",
                                params={"skip": skip, "limit": limit},
                            )
                            resp.raise_for_status()
                            data = resp.json()

                            items = data.get("items", [])
                            if not items:
                                page_success = True
                                break

                            for item in items:
                                messages.append(Message(**item))

                            skip += limit
                            pages_fetched += 1
                            page_success = True

                            if settings.bootstrap_max_pages and pages_fetched >= settings.bootstrap_max_pages:
                                break

                        except httpx.HTTPStatusError as e:
                            # Retry any HTTP error
                            retry_count += 1
                            if retry_count <= max_retries:
                                wait_time = min(retry_count * 2, 10)  # Exponential backoff, max 10s
                                log.warning(f"HTTP {e.response.status_code} at page {pages_fetched + 1}, retry {retry_count}/{max_retries} (waiting {wait_time}s)")
                                await asyncio.sleep(wait_time)
                            else:
                                log.error(f"Failed after {max_retries} retries at page {pages_fetched + 1}, skipping")
                                skip += limit  # Skip this page and try next
                                page_success = True
                        except (httpx.TimeoutException, httpx.NetworkError) as e:
                            retry_count += 1
                            if retry_count <= max_retries:
                                wait_time = min(retry_count * 2, 10)  # Exponential backoff, max 10s
                                log.warning(f"{type(e).__name__} at page {pages_fetched + 1}, retry {retry_count}/{max_retries} (waiting {wait_time}s)")
                                await asyncio.sleep(wait_time)
                            else:
                                log.error(f"Failed after {max_retries} retries at page {pages_fetched + 1}, skipping and continuing")
                                skip += limit  # Skip this page and try next
                                page_success = True
                        except Exception as e:
                            log.error(f"Unexpected error at page {pages_fetched + 1}: {type(e).__name__}: {e}")
                            raise

                    if hit_rate_limit or (page_success and not items):
                        break

            # Update dataset
            self.dataset.messages = messages
            self.dataset.refreshed_at = time.time()
            self.dataset.fetch_incomplete = hit_rate_limit

            if hit_rate_limit:
                log.info(f"Loaded {len(messages)} messages from upstream (incomplete - will retry in 5 min)")
            else:
                log.info(f"Loaded {len(messages)} messages from upstream")
            return messages
