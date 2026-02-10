import time


class DatasetStore:
    """
    Holds the upstream dataset in memory + timestamp.
    """
    def __init__(self):
        self.messages = []
        self.refreshed_at = 0.0
        self.fetch_incomplete = False

    def is_fresh(self, ttl_seconds: int) -> bool:
        if not self.messages:
            return False
        # If last fetch was incomplete, use shorter TTL (5 minutes)
        if self.fetch_incomplete:
            return (time.time() - self.refreshed_at) < 300
        return (time.time() - self.refreshed_at) < ttl_seconds
