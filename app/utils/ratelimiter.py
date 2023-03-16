from __future__ import annotations

import asyncio
import enum
import sys
import time
import traceback
import typing as t
from collections import deque


class BucketType(enum.IntEnum):
    """All possible ratelimiter bucket types."""

    GLOBAL = 0
    USER = 1
    TOKEN = 2


class RateLimiter:
    def __init__(self, period: float, limit: int, bucket: BucketType, wait: bool = True) -> None:
        """Rate Limiter implementation for Airy

        Parameters
        ----------
        period : float
            The period, in seconds, after which the quota resets.
        limit : int
            The amount of requests allowed in a quota.
        bucket : BucketType
            The bucket to handle this under.
        wait : bool
            Determines if the ratelimiter should wait in
            case of hitting a ratelimit.
        """
        self.period: float = period
        self.limit: int = limit
        self.bucket: BucketType = bucket
        self.wait: bool = False

        self._bucket_data = {}

        # deque is basically a list optimized for append and pop at begin&end
        self._queue: t.Deque[asyncio.Event] = deque()
        self._task: t.Optional[asyncio.Task[t.Any]] = None

    def _get_key(self, ctx) -> int:
        """Get key for cooldown bucket"""

        keys = {
            BucketType.GLOBAL: 0,
            BucketType.USER: (ctx.id, ctx.type, ctx.object_id)
        }

        return keys[self.bucket]

    def is_rate_limited(self, ctx) -> bool:
        """Returns a boolean determining if the ratelimiter is ratelimited or not."""
        now = time.monotonic()
        key = self._get_key(ctx)

        if bucket_item := self._bucket_data.get(key):
            if bucket_item["reset_at"] <= now:
                bucket_item["remaining"] = self.limit
                bucket_item["reset_at"] = now + self.period
                return False
            return bucket_item["remaining"] <= 0

        self._bucket_data[key] = {"reset_at": now + self.period, "remaining": self.limit}
        return False

    async def acquire(self, ctx) -> None:
        """Acquire a ratelimit, block execution if ratelimited and wait is True."""
        event = asyncio.Event()

        self._queue.append(event)

        if self._task is None:
            self._task = asyncio.create_task(self._iter_queue(ctx))

        if self.wait:
            await event.wait()

    async def _iter_queue(self, ctx) -> None:
        try:
            if not self._queue:
                self._task = None
                return

            if self.is_rate_limited(ctx):
                # Sleep until ratelimit expires
                key = self._get_key(ctx)
                bucket_item = self._bucket_data[key]
                sleep_time = bucket_item["reset_at"] - time.monotonic()
                await asyncio.sleep(sleep_time)

            # Set events while not ratelimited
            while not self.is_rate_limited(ctx) and self._queue:

                key = self._get_key(ctx)

                if bucket_item := self._bucket_data.get(key):
                    bucket_item["remaining"] -= 1
                else:
                    self._bucket_data[key] = {"reset_at": time.monotonic() + self.period, "remaining": self.limit - 1}

                self._queue.popleft().set()

            self._task = None

        except Exception as e:
            print(f"Task Exception was never retrieved: {e}", file=sys.stderr)
            print(traceback.format_exc(), file=sys.stderr)
