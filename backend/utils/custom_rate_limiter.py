from typing import Callable, Optional
from fastapi import Request, Depends
from starlette.responses import Response
from fastapi_limiter.depends import RateLimiter as OriginalRateLimiter
import os
import logging

logger = logging.getLogger(__name__)

class OptionalRateLimiter:
    """
    A wrapper around FastAPI Limiter that applies rate limiting only if
    Redis is properly configured. Otherwise, it works as a no-op.
    """
    
    def __init__(self, times: int = 1, seconds: Optional[int] = None, minutes: Optional[int] = None, hours: Optional[int] = None):
        """
        Initialize with the same parameters as RateLimiter, but make it optional.
        
        Args:
            times: Maximum number of requests allowed
            seconds: Within this many seconds
            minutes: Within this many minutes
            hours: Within this many hours
        """
        self.times = times
        self.seconds = seconds
        self.minutes = minutes
        self.hours = hours
        
        # Check if REDIS_URL is set - this is how we determine if rate limiting should be applied
        self.redis_available = bool(os.getenv("REDIS_URL"))
        
        # Only create the actual limiter if Redis is available
        if self.redis_available:
            self.limiter = OriginalRateLimiter(
                times=times, 
                seconds=seconds or 0, 
                minutes=minutes or 0, 
                hours=hours or 0
            )
        else:
            self.limiter = None
            logger.warning(
                f"Rate limiting disabled for endpoint (would have been limited to {times} requests per "
                f"{(seconds or 0) + (minutes or 0)*60 + (hours or 0)*3600} seconds). Set REDIS_URL to enable rate limiting."
            )
    
    async def __call__(self, request: Request, response: Response):
        """
        Apply rate limiting if Redis is available, otherwise just pass through.
        """
        if self.redis_available and self.limiter:
            # Apply the actual rate limiting, passing response
            await self.limiter(request, response)

# Helper function for cleaner usage
def rate_limit(times: int = 1, seconds: Optional[int] = None, minutes: Optional[int] = None, hours: Optional[int] = None):
    """
    Apply rate limiting conditionally based on Redis availability.
    Usage is the same as the original RateLimiter.
    
    Example:
        @router.post("/endpoint", dependencies=[Depends(rate_limit(times=5, minutes=1))])
    """
    return OptionalRateLimiter(times=times, seconds=seconds, minutes=minutes, hours=hours) 