"""
Rate limiting utilities for API calls.
Implements human-like delays to avoid bot detection.
"""

import time
import random
from typing import Optional
from functools import wraps
import structlog

from config.settings import get_settings

logger = structlog.get_logger(__name__)


class RateLimiter:
    """
    Rate limiter with random delays to appear human-like.
    Prevents bot detection by TikTok API.
    """

    def __init__(
        self,
        min_delay: Optional[float] = None,
        max_delay: Optional[float] = None,
        jitter: float = 0.2
    ):
        """
        Initialize rate limiter.

        Args:
            min_delay: Minimum delay between requests (seconds)
            max_delay: Maximum delay between requests (seconds)
            jitter: Random jitter factor (0.0 to 1.0)
        """
        settings = get_settings()

        self.min_delay = min_delay or settings.MIN_REQUEST_DELAY
        self.max_delay = max_delay or settings.MAX_REQUEST_DELAY
        self.jitter = jitter
        self.last_request_time = 0
        self.request_count = 0

        logger.info(
            "rate_limiter_initialized",
            min_delay=self.min_delay,
            max_delay=self.max_delay
        )

    def wait(self) -> float:
        """
        Wait before making next request.
        Adds random delay to appear human-like.

        Returns:
            float: Actual delay applied (seconds)
        """
        # Calculate time since last request
        elapsed = time.time() - self.last_request_time

        # Generate random delay with jitter
        base_delay = random.uniform(self.min_delay, self.max_delay)
        jitter_amount = base_delay * self.jitter * random.uniform(-1, 1)
        total_delay = max(0, base_delay + jitter_amount)

        # Apply delay if needed
        if elapsed < total_delay:
            sleep_time = total_delay - elapsed
            logger.debug(
                "rate_limit_waiting",
                sleep_time=round(sleep_time, 2),
                request_number=self.request_count + 1
            )
            time.sleep(sleep_time)
            actual_delay = total_delay
        else:
            actual_delay = elapsed

        # Update state
        self.last_request_time = time.time()
        self.request_count += 1

        return actual_delay

    def reset(self):
        """Reset rate limiter state."""
        self.last_request_time = 0
        self.request_count = 0
        logger.info("rate_limiter_reset")

    def get_stats(self) -> dict:
        """
        Get rate limiter statistics.

        Returns:
            dict: Statistics
        """
        return {
            "total_requests": self.request_count,
            "min_delay": self.min_delay,
            "max_delay": self.max_delay,
            "time_since_last_request": time.time() - self.last_request_time if self.last_request_time > 0 else None
        }


def rate_limited(min_delay: Optional[float] = None, max_delay: Optional[float] = None):
    """
    Decorator to apply rate limiting to functions.

    Usage:
        @rate_limited(min_delay=5, max_delay=10)
        def fetch_user_data(user_id):
            # API call here
            pass

    Args:
        min_delay: Minimum delay between calls
        max_delay: Maximum delay between calls
    """
    # Create a rate limiter instance for this decorator
    limiter = RateLimiter(min_delay=min_delay, max_delay=max_delay)

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Apply rate limiting
            delay = limiter.wait()

            # Call the function
            try:
                result = func(*args, **kwargs)
                logger.debug(
                    "rate_limited_call_success",
                    function=func.__name__,
                    delay_applied=round(delay, 2)
                )
                return result
            except Exception as e:
                logger.error(
                    "rate_limited_call_error",
                    function=func.__name__,
                    error=str(e)
                )
                raise

        return wrapper
    return decorator


class AdaptiveRateLimiter(RateLimiter):
    """
    Adaptive rate limiter that adjusts delays based on success/failure.
    Increases delays when errors occur, decreases when successful.
    """

    def __init__(
        self,
        min_delay: Optional[float] = None,
        max_delay: Optional[float] = None,
        backoff_factor: float = 1.5,
        recovery_factor: float = 0.9
    ):
        """
        Initialize adaptive rate limiter.

        Args:
            min_delay: Minimum delay between requests
            max_delay: Maximum delay between requests
            backoff_factor: Multiplier for delay on error (> 1.0)
            recovery_factor: Multiplier for delay on success (< 1.0)
        """
        super().__init__(min_delay, max_delay)
        self.backoff_factor = backoff_factor
        self.recovery_factor = recovery_factor
        self.current_delay = self.min_delay
        self.error_count = 0
        self.success_count = 0

    def report_success(self):
        """Report successful request to decrease delay."""
        self.success_count += 1
        self.error_count = 0  # Reset error count on success

        # Gradually reduce delay on consecutive successes
        if self.success_count >= 3:
            self.current_delay = max(
                self.min_delay,
                self.current_delay * self.recovery_factor
            )
            self.success_count = 0
            logger.info(
                "rate_limiter_decreased_delay",
                new_delay=round(self.current_delay, 2)
            )

    def report_error(self, error_type: str = "unknown"):
        """Report failed request to increase delay."""
        self.error_count += 1
        self.success_count = 0  # Reset success count on error

        # Increase delay on error
        self.current_delay = min(
            self.max_delay,
            self.current_delay * self.backoff_factor
        )

        logger.warning(
            "rate_limiter_increased_delay",
            error_type=error_type,
            error_count=self.error_count,
            new_delay=round(self.current_delay, 2)
        )

    def wait(self) -> float:
        """Wait with adaptive delay."""
        elapsed = time.time() - self.last_request_time

        # Use current adaptive delay instead of random
        total_delay = self.current_delay

        if elapsed < total_delay:
            sleep_time = total_delay - elapsed
            time.sleep(sleep_time)
            actual_delay = total_delay
        else:
            actual_delay = elapsed

        self.last_request_time = time.time()
        self.request_count += 1

        return actual_delay


if __name__ == "__main__":
    # Test rate limiter
    print("Testing RateLimiter...")

    limiter = RateLimiter(min_delay=1, max_delay=2)

    print("\nMaking 5 rate-limited requests...")
    for i in range(5):
        start = time.time()
        delay = limiter.wait()
        duration = time.time() - start

        print(f"Request {i+1}: waited {duration:.2f}s (target delay: {delay:.2f}s)")

    print(f"\nStats: {limiter.get_stats()}")

    # Test adaptive rate limiter
    print("\n\nTesting AdaptiveRateLimiter...")
    adaptive = AdaptiveRateLimiter(min_delay=1, max_delay=5)

    print("\nSimulating errors (delay should increase)...")
    for i in range(3):
        adaptive.wait()
        adaptive.report_error("test_error")
        print(f"  After error {i+1}: delay = {adaptive.current_delay:.2f}s")

    print("\nSimulating successes (delay should decrease)...")
    for i in range(5):
        adaptive.wait()
        adaptive.report_success()
        print(f"  After success {i+1}: delay = {adaptive.current_delay:.2f}s")

    print("\n✓ Rate limiter tests complete!")
