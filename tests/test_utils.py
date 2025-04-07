import pytest
from cec_control._utils import MemoryCache, Time, Wait


class TimeMock:
    def __init__(self, ts=0):
        self._ts = ts
        self._ts_fn = None

    def set(self, ts):
        self._ts = ts

    def __enter__(self):
        self._ts_fn = Time.ts
        Time.ts = lambda: self._ts
        return self.set

    def __exit__(self, *exc_info) -> None:
        Time.ts = self._ts_fn


def test__MemoryCache_should_store_val():
    cache = MemoryCache()
    assert cache.has("A") is False
    cache.set("A", 10)
    assert cache.has("A") is True
    assert cache.get("A") is 10


def test__MemoryCache_should_get_set():
    cache = MemoryCache()
    cache.get_or_set("B", 10)
    assert cache._get("B") == 10
    cache.remove("B")
    cache.get_or_set("B", lambda: "val")
    assert cache._get("B") == "val"


def test__MemoryCache_should_expire():
    with TimeMock(1.0) as set_ts:
        cache = MemoryCache()
        cache.set("C", 1, 1.5)
        set_ts(2.4999999999)
        assert cache.has("C") is True
        set_ts(2.5000000001)
        assert cache.has("C") is False


def test__Wait_should_check_time():
    with TimeMock(1.0) as set_ts:
        _w = Wait(2, 10)
        assert _w.end_time == 3.0
        assert _w.max_count == 10
        assert _w.sleep_sec == 0

        set_ts(2.999)
        assert _w.waiting is True

        set_ts(3.000)
        assert _w.waiting is False


def test__Wait_should_check_count():
    with TimeMock() as set_ts:
        _w = Wait(1, 4)
        _w.tick()
        _w.tick()
        _w.tick()
        assert _w.waiting is True
        _w.tick()
        assert _w.waiting is False


def test__Wait_should_wait_for():
    x = 0
    r = Wait.for_fn(10, lambda: x)
    assert r == 0
