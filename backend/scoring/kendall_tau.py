"""Kendall tau distance implementation.

Computes the number of pairwise inversions (discordant pairs) between
two rankings, which represents the minimum number of adjacent swaps
needed to transform one ranking into the other.
"""


def kendall_tau_distance(ranking_a: list[int], ranking_b: list[int]) -> int:
    """Compute the Kendall tau distance between two rankings.

    The Kendall tau distance counts the number of pairwise disagreements
    between the two orderings. Both rankings must be permutations of the
    same set of elements.

    Args:
        ranking_a: First ranking as an ordered list of element identifiers.
        ranking_b: Second ranking as an ordered list of element identifiers.

    Returns:
        The number of discordant pairs (pairwise inversions) between the
        two rankings. Guaranteed to be in [0, N*(N-1)/2] where N is the
        length of the rankings.

    Raises:
        ValueError: If rankings have different lengths or contain different elements.
    """
    if len(ranking_a) != len(ranking_b):
        raise ValueError(
            f"Rankings must have the same length: got {len(ranking_a)} and {len(ranking_b)}"
        )

    if set(ranking_a) != set(ranking_b):
        raise ValueError("Rankings must contain the same set of elements")

    n = len(ranking_a)
    if n <= 1:
        return 0

    # Build position map for ranking_b: element -> position in ranking_b
    pos_b = {element: idx for idx, element in enumerate(ranking_b)}

    # Count inversions: for each pair (i, j) where i < j in ranking_a,
    # check if their relative order is reversed in ranking_b
    inversions = 0
    for i in range(n):
        for j in range(i + 1, n):
            # Elements at positions i and j in ranking_a
            elem_i = ranking_a[i]
            elem_j = ranking_a[j]
            # If their order is reversed in ranking_b, that's an inversion
            if pos_b[elem_i] > pos_b[elem_j]:
                inversions += 1

    return inversions
