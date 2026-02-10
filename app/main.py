from __future__ import annotations

import asyncio
import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse

from .cache import DatasetStore
from .config import settings
from .index import search_messages
from .models import SearchResponse
from .message_client import MessagesClient

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("search_service")

dataset = DatasetStore()
messages_client = MessagesClient(dataset)


async def _refresh_dataset_if_needed(force: bool = False):
    """Refresh dataset from upstream if needed."""
    if force or not dataset.is_fresh(settings.cache_ttl_seconds):
        await messages_client.fetch_all_messages(force=force)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for the application."""
    # Startup: warm up the cache
    log.info("Starting up...")
    try:
        await messages_client.fetch_all_messages()
        log.info(f"Loaded {len(dataset.messages)} messages")
    except Exception as e:
        log.error(f"Warning: Failed to warm up cache: {e}")

    yield

    # Shutdown: cleanup
    log.info("Shutting down...")


app = FastAPI(
    default_response_class=JSONResponse,
    title="Messages Search API",
    version="1.0.0",
    lifespan=lifespan,
)

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "ok": True,
        "messages_loaded": len(dataset.messages),
        "dataset_fresh": dataset.is_fresh(settings.cache_ttl_seconds),
        "refreshed_at": dataset.refreshed_at,
    }


@app.get("/search", response_model=SearchResponse)
async def search(
    query: str = Query(..., min_length=1, description="Search query"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1),
    refresh: bool = Query(False, description="Force refresh from upstream before searching"),
):
    """
    Search messages endpoint.

    Searches across all fields in messages and returns paginated results.
    """
    start_time = time.time()

    # Refresh dataset if needed
    await _refresh_dataset_if_needed(force=refresh)

    # Perform search
    hits = search_messages(dataset.messages, query)
    total = len(hits)
    items = hits[skip : skip + limit]

    elapsed_ms = (time.time() - start_time) * 1000

    resp = SearchResponse(
        query=query,
        skip=skip,
        limit=limit,
        total=total,
        items=items,
        refreshed_at=dataset.refreshed_at,
        response_time_ms=elapsed_ms,
    )

    log.info(f"Search for '{query}' returned {total} results - {elapsed_ms:.2f}ms")

    return resp


@app.get("/cache/stats")
async def cache_stats():
    """Get cache statistics."""
    return {
        "dataset": {
            "messages_count": len(dataset.messages),
            "is_fresh": dataset.is_fresh(settings.cache_ttl_seconds),
            "refreshed_at": dataset.refreshed_at,
        },
    }
