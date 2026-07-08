import time
import logging
import threading
from fastapi import Request, HTTPException, status

from src.config.config import settings

logger = logging.getLogger(__name__)


class TokenBucketLimiter:
    """
    Thread-safe implementation of a Token Bucket Rate Limiter.
    Limits requests based on unique keys (e.g. user ID or IP address).
    """
    def __init__(self, requests_per_minute: int = settings.RATE_LIMIT_ASK_PER_MIN):
        self.capacity = float(requests_per_minute)
        self.refill_rate = self.capacity / 60.0  # tokens per second
        self.buckets = {}
        self.lock = threading.Lock()

    def check_rate_limit(self, key: str) -> None:
        """
        Check if the key is allowed to make a request.
        Raises HTTPException with 429 status code if limit is exceeded.
        """
        now = time.time()
        with self.lock:
            if key not in self.buckets:
                self.buckets[key] = {
                    "tokens": self.capacity,
                    "last_updated": now
                }

            bucket = self.buckets[key]
            elapsed = now - bucket["last_updated"]
            bucket["last_updated"] = now

            # Refill bucket based on time elapsed
            bucket["tokens"] = min(self.capacity, bucket["tokens"] + elapsed * self.refill_rate)

            # Consume token
            if bucket["tokens"] >= 1.0:
                bucket["tokens"] -= 1.0
                logger.debug(f"RateLimiter: Consumed 1 token for key={key}. Remaining: {bucket['tokens']:.2f}")
            else:
                logger.warning(f"RateLimiter: Limit exceeded for key={key}. Blocked.")
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many requests. Please wait a moment before trying again."
                )


# Global rate limiter instance
ask_limiter = TokenBucketLimiter()


def rate_limit_ask(request: Request) -> None:
    """
    FastAPI dependency to rate limit /ask or other endpoints.
    Identifies requests using client host IP address or authorization context.
    """
    client_ip = request.client.host if request.client else "unknown"
    # Key on client IP for simple anonymous rate limiting
    ask_limiter.check_rate_limit(client_ip)
