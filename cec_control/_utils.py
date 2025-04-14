import time
from typing import Callable, Generic, TypeVar

MAX_TRACE_COUNT = 1000000
T = TypeVar("T")


class CancellationToken:
    def __init__(self):
        self.is_running = True
        self.action = lambda: None

    @property
    def is_cancelled(self):
        return not self.is_running

    def cancel(self):
        if self.is_running:
            self.is_running = False
            self.action()


TKey = str | int | bool
TVal = str | int | bool | float


class Time:
    @staticmethod
    def ts():
        return time.monotonic()

    @staticmethod
    def sleep(sec: float):
        if sec > 0:
            time.sleep(sec)


class MemoryCache:
    def __init__(self):
        self.cache = {}

    def has(self, key: TKey):
        """Check if a valid (non-expired) key exists in the cache."""
        if key in self.cache:
            _, expires_at = self.cache[key]
            if expires_at is None or Time.ts() < expires_at:
                return True
            else:
                del self.cache[key]  # Clean up expired key

        return False

    def set(self, key: TKey, value: TVal, ttl=0.0):
        """Set a value with a TTL (in seconds)."""
        expire_at = None if ttl is None or ttl <= 0 else Time.ts() + ttl
        self.cache[key] = (value, expire_at)

    def get(self, key: TKey, default_value=None):
        return self._get(key) if self.has(key) else default_value

    def remove(self, key: TKey):
        """Removes a cached value"""
        del self.cache[key]

    def get_or_set(self, key: TKey, value: TVal | Callable[[], TVal], ttl=0.0):
        """Return cached value if valid; otherwise, store and return new value."""
        if self.has(key):
            return self._get(key)

        if callable(value):
            value = value()

        self.set(key, value, ttl)
        return value

    def _get(self, key: TKey):
        return self.cache[key][0]


def check_not_none(x):
    return x is not None


class Wait:
    @staticmethod
    def for_fn(
        seconds: int,
        fn: Callable[[], bool],
        token: CancellationToken = None,
        sleep_sec=0,
        max_count=None,
    ):
        token = CancellationToken() if token is None else token
        wt = Wait(seconds, max_count=max_count, sleep_sec=sleep_sec)
        while token.is_running and wt.waiting:
            if fn():
                return True
            else:
                wt.tick()

        return False

    def __init__(self, max_sec: float, max_count: int | None = None, sleep_sec=0.0):
        if max_count is None:
            max_count = MAX_TRACE_COUNT

        self.end_time = Time.ts() + max_sec
        self.count = 0
        self.max_count = max_count
        self.sleep_sec = sleep_sec
        self._last_ts = None

    @property
    def waiting(self):
        self._last_ts = Time.ts()
        return self._last_ts < self.end_time and self.count < self.max_count

    def tick(self):
        Time.sleep(self.sleep_sec)
        self.count += 1

    def __repr__(self):
        return f"{self._last_ts}"


def to_enum(value: int | str, enum_cls: Generic[T], default_val: T = None) -> T:
    return enum_cls(value) if value in enum_cls._value2member_map_ else default_val
