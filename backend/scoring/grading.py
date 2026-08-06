"""Letter grade assignment based on Kendall tau distance.

Maps a numeric distance score to a letter grade using fixed thresholds:
  S = 0 (perfect match)
  A = 1-2 (near perfect)
  B = 3-4 (solid)
  C = 5-6 (mediocre)
  D = 7+  (far off)
"""


def letter_grade(distance: int) -> str:
    """Assign a letter grade based on Kendall tau distance.

    Args:
        distance: The Kendall tau distance (non-negative integer).

    Returns:
        A letter grade string: one of "S", "A", "B", "C", "D".

    Raises:
        ValueError: If distance is negative.
    """
    if distance < 0:
        raise ValueError(f"Distance must be non-negative, got {distance}")

    if distance == 0:
        return "S"
    elif distance <= 2:
        return "A"
    elif distance <= 4:
        return "B"
    elif distance <= 6:
        return "C"
    else:
        return "D"
