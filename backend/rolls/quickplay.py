"""Quick Play Roll generation with deduplication.

Generates random Rolls for on-demand play, ensuring the new Roll
does not duplicate the user's most recent 5 Quick Play Rolls.
"""

import json

import redis.asyncio as redis

from .generator import generate_roll

# Maximum number of recent rolls to track per user for deduplication
MAX_RECENT_ROLLS = 5

# Maximum attempts to generate a unique roll before giving up
MAX_GENERATION_ATTEMPTS = 50


def _roll_key(roll: dict[str, str]) -> str:
    """Create a deduplication key from a Roll's position and theme_modifier."""
    return f"{roll['position']}|{roll['theme_modifier']}"


async def generate_quickplay_roll(
    user_id: str | None,
    redis_client: redis.Redis,
) -> dict[str, str]:
    """Generate a Quick Play Roll that avoids the user's recent rolls.

    Checks the Redis list `user:recent_rolls:{user_id}` to find the
    user's last 5 Quick Play Rolls, then generates a new Roll that
    differs in at least position or theme modifier from all of them.

    If user_id is None (anonymous user), no deduplication is performed.

    Args:
        user_id: The user's identifier. None for anonymous users.
        redis_client: An async Redis client instance.

    Returns:
        A Roll dictionary with "position" and "theme_modifier" keys.
    """
    recent_keys: set[str] = set()

    # Load recent rolls for deduplication
    if user_id is not None:
        list_key = f"user:recent_rolls:{user_id}"
        recent_raw = await redis_client.lrange(list_key, 0, MAX_RECENT_ROLLS - 1)
        recent_keys = {item.decode() if isinstance(item, bytes) else item for item in recent_raw}

    # Generate a roll that doesn't match recent history
    for _ in range(MAX_GENERATION_ATTEMPTS):
        roll = generate_roll()
        key = _roll_key(roll)
        if key not in recent_keys:
            break
    # If all attempts exhausted, we still return the last generated roll
    # (edge case when user has played most combinations recently)

    # Record this roll in the user's recent history
    if user_id is not None:
        list_key = f"user:recent_rolls:{user_id}"
        key = _roll_key(roll)
        await redis_client.lpush(list_key, key)
        await redis_client.ltrim(list_key, 0, MAX_RECENT_ROLLS - 1)

    return roll
