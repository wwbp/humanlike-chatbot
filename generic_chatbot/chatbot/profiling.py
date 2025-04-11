import cProfile
import pstats
import io
import functools
import logging


def profile_view(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        pr = cProfile.Profile()
        pr.enable()
        result = await func(*args, **kwargs)
        pr.disable()
        s = io.StringIO()
        ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
        ps.print_stats(10)  # prints top 10 time-consuming functions
        logging.info("Profiling report for %s: \n%s",
                     func.__name__, s.getvalue())
        return result
    return wrapper
