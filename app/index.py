from typing import List
from .models import Message


def search_messages(messages: List[Message], query: str) -> List[Message]:
    """
    Simple substring search across all message fields.
    Returns all messages containing the query string (case-insensitive).
    """
    query_lower = query.strip().lower()
    if not query_lower:
        return []

    hits = []

    for msg in messages:
        # Check if query appears in any field
        if (
            (msg.message and query_lower in msg.message.lower())
            or (msg.user_name and query_lower in msg.user_name.lower())
            or (msg.user_id and query_lower in msg.user_id.lower())
            or (msg.id and query_lower in msg.id.lower())
            or (msg.timestamp and query_lower in msg.timestamp.lower())
        ):
            hits.append(msg)

    return hits
