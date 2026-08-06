"""Daily Challenge generation and caching.

Generates one fixed Roll per calendar day (UTC) and caches it in Redis
so that all users receive the identical challenge for that day.
"""

import json
from datetime import date, datetime, timezone, timedelta

import redis.asyncio as redis

from .generator import generate_roll


async def get_daily_challenge(
    target_date: date,
    redis_client: redis.Redis,
) -> dict[str, str]:
    """Get or generate the daily challenge Roll for a given date.

    If a Roll for the given date already exists in Redis, it is returned
    from cache. Otherwise, a new Roll is generated, cached in Redis with
    a TTL lasting until the end of the UTC day, and returned.

    Args:
        target_date: The calendar date (UTC) for the daily challenge.
        redis_client: An async Redis client instance.

    Returns:
        A Roll dictionary with "position" and "theme_modifier" keys.
    """
    cache_key = f"daily_challenge:{target_date.isoformat()}"

    # Try to retrieve from cache
    cached = await redis_client.get(cache_key)
    if cached is not None:
        return json.loads(cached)

    # Generate a new Roll for this date
    # Use date as seed for deterministic generation across instances
    import random

    rng = random.Random(f"daily_{target_date.isoformat()}")
    from .generator import POSITIONS, THEME_MODIFIERS

    position = rng.choice(POSITIONS)
    theme_modifier = rng.choice(THEME_MODIFIERS)

    roll = {
        "position": position,
        "theme_modifier": theme_modifier,
    }

    # Compute TTL: seconds remaining until end of UTC day
    now_utc = datetime.now(timezone.utc)
    end_of_day = datetime.combine(
        target_date + timedelta(days=1),
        datetime.min.time(),
        tzinfo=timezone.utc,
    )
    ttl_seconds = max(int((end_of_day - now_utc).total_seconds()), 1)

    # Cache in Redis
    await redis_client.set(cache_key, json.dumps(roll), ex=ttl_seconds)

    return roll
