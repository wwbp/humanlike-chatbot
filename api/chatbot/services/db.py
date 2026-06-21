"""Shared DB-resilience helpers for the async / thread-sensitive stack."""

import logging

from django.db import InterfaceError, OperationalError, connection

logger = logging.getLogger(__name__)


def db_retry(fn, *args, **kwargs):
    """
    Run a synchronous DB callable, reconnecting once if the connection is stale.

    Under the ASGI + sync_to_async stack a pooled MySQL connection can linger on
    its worker thread, get reaped server-side during an idle gap, and raise on
    its next use:
        (2006, 'Server has gone away')
        (4031, '... disconnected by the server because of inactivity ...')
        (2013, 'Lost connection to server during query')
    CONN_HEALTH_CHECKS is a no-op at CONN_MAX_AGE=0 (Django only health-checks
    persistent connections), so nothing pings these. On that failure we close the
    *current thread's* connection and retry once on a fresh socket.

    Acting on the calling thread is what makes this work for DB queries on
    thread_sensitive=False threads (e.g. moderation), whose connection neither
    _recycle_db_connections() nor Django's request teardown ever touches — that
    was the real source of the recurring first-query 500s.

    Retrying is safe for reads; for a write it risks a rare duplicate if the
    server committed before the socket dropped, which is preferable to a 500.
    """
    try:
        return fn(*args, **kwargs)
    except (OperationalError, InterfaceError) as e:
        logger.warning(
            "Stale DB connection on %s (%s); reconnecting and retrying once",
            getattr(fn, "__name__", fn),
            e,
        )
        connection.close()
        return fn(*args, **kwargs)
