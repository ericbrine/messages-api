from typing import Any, Optional
from pydantic import BaseModel, Field


class Message(BaseModel):
    id: Optional[str] = None
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    message: Optional[str] = None
    timestamp: Optional[str] = None

    model_config = {"extra": "allow"}


class SearchResponse(BaseModel):
    query: str
    skip: int
    limit: int
    total: int
    items: list[Message]
    refreshed_at: float
    response_time_ms: float


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Service status")
