"""Async tests for Daily Challenge and Quick Play Roll generation."""

import json
from datetime import date, timezone, datetime
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio

from rolls.daily import get_daily_challenge
from rolls.quickplay import generate_quickplay_roll


class FakeRedis:
    """Minimal fake async Redis for testing."""

    def __init__(self):
        self.store: dict[str, str] = {}
        self.lists: dict[str, list[str]] = {}

    async def get(self, key: str) -> str | None:
        return self.store.get(key)

    async def set(self, key: str, value: str, ex: int | None = None):
        self.store[key] = value

    async def lrange(self, key: str, start: int, stop: int) -> list[str]:
        lst = self.lists.get(key, [])
        return lst[start:stop + 1]

    async def lpush(self, key: str, *values: str):
        if key not in self.lists:
            self.lists[key] = []
        for v in reversed(values):
            self.lists[key].insert(0, v)

    async def ltrim(self, key: str, start: int, stop: int):
        if key in self.lists:
            self.lists[key] = self.lists[key][start:stop + 1]


@pytest.fixture
def fake_redis():
    return FakeRedis()


class TestDailyChallenge:
    """Tests for get_daily_challenge."""

    @pytest.mark.asyncio
    async def test_generates_roll_for_date(self, fake_redis):
        today = date(2024, 6, 15)
        roll = await get_daily_challenge(today, fake_redis)
        assert "position" in roll
        assert "theme_modifier" in roll

    @pytest.mark.asyncio
    async def test_caches_roll_in_redis(self, fake_redis):
        today = date(2024, 6, 15)
        await get_daily_challenge(today, fake_redis)
        cache_key = f"daily_challenge:{today.isoformat()}"
        assert cache_key in fake_redis.store

    @pytest.mark.asyncio
    async def test_returns_same_roll_on_second_call(self, fake_redis):
        today = date(2024, 6, 15)
        roll1 = await get_daily_challenge(today, fake_redis)
        roll2 = await get_daily_challenge(today, fake_redis)
        assert roll1 == roll2

    @pytest.mark.asyncio
    async def test_different_dates_can_produce_different_rolls(self, fake_redis):
        # Not guaranteed to be different, but the seeding mechanism makes it likely
        roll1 = await get_daily_challenge(date(2024, 1, 1), fake_redis)
        roll2 = await get_daily_challenge(date(2024, 12, 31), fake_redis)
        # At least verify they are both valid
        from rolls.generator import POSITIONS, THEME_MODIFIERS
        assert roll1["position"] in POSITIONS
        assert roll2["position"] in POSITIONS


class TestQuickPlay:
    """Tests for generate_quickplay_roll."""

    @pytest.mark.asyncio
    async def test_generates_roll_anonymous(self, fake_redis):
        roll = await generate_quickplay_roll(None, fake_redis)
        assert "position" in roll
        assert "theme_modifier" in roll

    @pytest.mark.asyncio
    async def test_generates_roll_authenticated(self, fake_redis):
        roll = await generate_quickplay_roll("user-123", fake_redis)
        assert "position" in roll
        assert "theme_modifier" in roll

    @pytest.mark.asyncio
    async def test_stores_in_recent_history(self, fake_redis):
        await generate_quickplay_roll("user-123", fake_redis)
        list_key = "user:recent_rolls:user-123"
        assert list_key in fake_redis.lists
        assert len(fake_redis.lists[list_key]) == 1

    @pytest.mark.asyncio
    async def test_recent_history_capped_at_5(self, fake_redis):
        for _ in range(10):
            await generate_quickplay_roll("user-123", fake_redis)
        list_key = "user:recent_rolls:user-123"
        assert len(fake_redis.lists[list_key]) <= 5

    @pytest.mark.asyncio
    async def test_avoids_recent_rolls(self, fake_redis):
        # Pre-seed recent rolls with a specific combo
        list_key = "user:recent_rolls:user-456"
        fake_redis.lists[list_key] = ["PG|All-Time"]

        # Generate many rolls, none should match the seeded one
        # (probabilistic but with 42 combinations vs 1, extremely likely)
        rolls = []
        for _ in range(20):
            roll = await generate_quickplay_roll("user-456", fake_redis)
            key = f"{roll['position']}|{roll['theme_modifier']}"
            rolls.append(key)

        # The first generated roll should not be "PG|All-Time"
        # (it's in recent history at time of first generation)
        assert rolls[0] != "PG|All-Time"
