"""
retry.py
--------
Reliability & Resilience Helper Module implementing Exponential Backoff Retries
for transient database connection failures and network glitches.
"""

import logging
import time
from typing import Any, Callable, Tuple, Type

from database.exceptions import PermanentDatabaseError, TransientDatabaseError

logger = logging.getLogger(__name__)


def execute_with_retry(
    func: Callable[..., Any],
    *args: Any,
    max_retries: int = 3,
    initial_delay: float = 0.1,
    backoff_factor: float = 2.0,
    retryable_exceptions: Tuple[Type[Exception], ...] = (TransientDatabaseError,),
    **kwargs: Any,
) -> Any:
    """
    Executes a callable with exponential backoff retries for transient failures.

    :param func: Function to execute.
    :param max_retries: Maximum retry attempts before raising.
    :param initial_delay: Initial delay in seconds.
    :param backoff_factor: Multiplier applied to delay after each retry.
    :param retryable_exceptions: Tuple of exception types eligible for retry.
    :return: Return value of successful function execution.
    """
    delay = initial_delay
    attempt = 1

    while True:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if isinstance(e, PermanentDatabaseError):
                logger.error("Non-retryable PermanentDatabaseError encountered. Failing fast: %s", str(e))
                raise e

            if not isinstance(e, retryable_exceptions) and not any(
                isinstance(e, exc_cls) for exc_cls in retryable_exceptions
            ):
                logger.error("Non-retryable exception type %s encountered. Failing fast.", type(e).__name__)
                raise e

            if attempt > max_retries:
                logger.error(
                    "Exhausted all %d retry attempts for %s. Last error: %s",
                    max_retries,
                    func.__name__,
                    str(e),
                )
                raise e

            logger.warning(
                "Transient failure on attempt %d/%d for %s: %s. Retrying in %.2fs...",
                attempt,
                max_retries,
                func.__name__,
                str(e),
                delay,
            )
            time.sleep(delay)
            delay *= backoff_factor
            attempt += 1
