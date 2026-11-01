import time
import functools
import logging

logging.basicConfig(level=logging.INFO, format="%(message)s")

def timed(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        logging.info(f"[{func.__name__}] виконано за {end - start:.6f} сек")
        return result
    return wrapper