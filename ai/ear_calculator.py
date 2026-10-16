from __future__ import annotations

import math
from typing import Iterable, Sequence


def calculate_ear(
    eye_landmarks: Sequence[tuple[float, float]] | Iterable[tuple[float, float]] | None,
) -> float:
    """Calculate the Eye Aspect Ratio for a six-point eye contour.

    The accepted eye contour is ordered as two eye corners and two upper/lower
    pairs: ``[corner, upper-left, upper-right, corner, lower-right, lower-left]``.
    """
    if eye_landmarks is None:
        return 0.0

    try:
        points = list(eye_landmarks)
    except TypeError:
        return 0.0

    if len(points) != 6:
        return 0.0

    p1, p2, p3, p4, p5, p6 = points
    vertical_1 = math.dist(p2, p6)
    vertical_2 = math.dist(p3, p5)
    horizontal = math.dist(p1, p4)

    if horizontal <= 1e-9:
        return 0.0

    return max(0.0, min(float((vertical_1 + vertical_2) / (2.0 * horizontal)), 1.0))

