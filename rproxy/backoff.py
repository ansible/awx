import random
import time
from typing import Callable


def exponential_backoff(
    attempt: int,
    base_delay: int = 2,
    jitter: float = 0.1,
    start_delay: int = 0,
    sleep_fn: Callable[[float], None] = time.sleep,
):
    """
    Implements an exponential backoff delay strategy with optional jitter and a start delay offset.

    Args:
        attempt (int): The current attempt number.
        base_delay (int): The base delay in seconds. Defaults to 2.
        jitter (float): The jitter coefficient to add randomness to the delay. Defaults to 0.1.
        start_delay (int): An additional delay offset in seconds. Defaults to 0.
        sleep_fn (Callable[[float], None], optional): A function to handle sleeping.
            Defaults to None, which uses a no-op.
    """
    delay = base_delay * (2 ** (attempt - 1))
    jitter_value = random.uniform(0, jitter * delay)
    delay_with_jitter = max(0, delay + jitter_value + start_delay)  # Ensure delay is not negative
    sleep_fn(delay_with_jitter)


# __all__ = ['exponential_backoff']
