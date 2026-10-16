from __future__ import annotations

from typing import Any

import cv2


LEFT_EYE_INDICES = [
    33, 160, 158, 133, 153, 144,
]
RIGHT_EYE_INDICES = [
    362, 385, 387, 263, 373, 380,
]


class EyeDetector:
    """Extract and draw eye landmarks from a MediaPipe face mesh."""

    def __init__(self):
        self.left_eye_landmarks: list[tuple[int, int]] = []
        self.right_eye_landmarks: list[tuple[int, int]] = []

    def extract_eye_landmarks(self, landmarks: Any, frame_shape: tuple[int, int, int]) -> tuple[list[tuple[int, int]], list[tuple[int, int]]]:
        if landmarks is None:
            return [], []

        h, w, _ = frame_shape
        left_points = []
        right_points = []

        point_data = getattr(landmarks, "landmark", landmarks)
        if not point_data:
            return [], []

        try:
            for index in LEFT_EYE_INDICES:
                landmark = point_data[index]
                left_points.append((int(landmark.x * w), int(landmark.y * h)))

            for index in RIGHT_EYE_INDICES:
                landmark = point_data[index]
                right_points.append((int(landmark.x * w), int(landmark.y * h)))
        except (IndexError, TypeError, AttributeError):
            return [], []

        self.left_eye_landmarks = left_points
        self.right_eye_landmarks = right_points
        return left_points, right_points

    def draw_eye_landmarks(self, frame: Any, landmarks: Any) -> Any:
        if frame is None or landmarks is None:
            return frame

        h, w, _ = frame.shape
        left_points, right_points = self.extract_eye_landmarks(landmarks, (h, w, 3))

        for point in left_points:
            cv2.circle(frame, point, 2, (0, 255, 255), -1)
        for point in right_points:
            cv2.circle(frame, point, 2, (255, 165, 0), -1)

        return frame

    def get_left_eye_coordinates(self, landmarks: Any, frame_shape: tuple[int, int, int]) -> list[tuple[int, int]]:
        left, _ = self.extract_eye_landmarks(landmarks, frame_shape)
        return left

    def get_right_eye_coordinates(self, landmarks: Any, frame_shape: tuple[int, int, int]) -> list[tuple[int, int]]:
        _, right = self.extract_eye_landmarks(landmarks, frame_shape)
        return right
