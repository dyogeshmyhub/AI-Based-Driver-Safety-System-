from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import cv2

try:
    import mediapipe as mp
except ImportError:  # pragma: no cover - unavailable in minimal test environments
    mp = None


@dataclass
class FaceDetectionResult:
    face_detected: bool
    faces_count: int
    landmarks: list[Any] = field(default_factory=list)
    message: str = ""


def get_primary_face_landmarks(result: Any) -> list[Any] | None:
    """Return the first detected face from a MediaPipe result without crashing."""
    if result is None:
        return None
    if hasattr(result, "face_landmarks"):
        faces = getattr(result, "face_landmarks")
        if not faces:
            return None
        return faces[0]
    if isinstance(result, list) and result:
        return result[0]
    return None


class FaceDetector:
    def __init__(
        self,
        max_faces: int = 1,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
    ):
        self.max_faces = max_faces
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence
        self.face_landmarker = None
        self.mp_available = False
        self.last_timestamp_ms = 0

        if mp is None or not hasattr(mp, "tasks"):
            return

        model_path = Path(__file__).resolve().parent / "models" / "face_landmarker.task"
        if not model_path.is_file():
            raise FileNotFoundError(f"MediaPipe face landmarker model not found: {model_path}")

        options = mp.tasks.vision.FaceLandmarkerOptions(
            base_options=mp.tasks.BaseOptions(model_asset_path=str(model_path)),
            running_mode=mp.tasks.vision.RunningMode.VIDEO,
            num_faces=max_faces,
            min_face_detection_confidence=min_detection_confidence,
            min_face_presence_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )
        self.face_landmarker = mp.tasks.vision.FaceLandmarker.create_from_options(options)
        self.mp_available = True

    def process_frame(self, frame):
        if frame is None:
            return FaceDetectionResult(False, 0, [], "NO DRIVER FACE DETECTED")

        if not self.mp_available or self.face_landmarker is None:
            return FaceDetectionResult(False, 0, [], "NO DRIVER FACE DETECTED")

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        timestamp_ms = max(int(time.monotonic() * 1000), self.last_timestamp_ms + 1)
        self.last_timestamp_ms = timestamp_ms
        results = self.face_landmarker.detect_for_video(image, timestamp_ms)
        faces = results.face_landmarks

        if not faces:
            return FaceDetectionResult(False, 0, [], "NO DRIVER FACE DETECTED")
        if len(faces) > 1:
            return FaceDetectionResult(False, len(faces), list(faces), "MULTIPLE FACES DETECTED")

        return FaceDetectionResult(True, 1, list(faces), "FACE DETECTED")

    def draw_landmarks(self, frame, landmarks):
        if frame is None or not landmarks:
            return frame

        if self.mp_available and self.face_landmarker is not None:
            for face_landmarks in landmarks:
                for landmark in face_landmarks:
                    x = int(landmark.x * frame.shape[1])
                    y = int(landmark.y * frame.shape[0])
                    cv2.circle(frame, (x, y), 1, (0, 255, 0), 1)
            return frame
        return frame

    def draw_face_box(self, frame, landmarks):
        if frame is None or not landmarks:
            return frame

        if self.mp_available and self.face_landmarker is not None:
            face_landmarks = landmarks[0]
            points = []
            for landmark in face_landmarks:
                x = int(landmark.x * frame.shape[1])
                y = int(landmark.y * frame.shape[0])
                points.append((x, y))

            if not points:
                return frame

            x_values = [point[0] for point in points]
            y_values = [point[1] for point in points]
            min_x, min_y = min(x_values), min(y_values)
            max_x, max_y = max(x_values), max(y_values)
            cv2.rectangle(frame, (min_x, min_y), (max_x, max_y), (0, 255, 255), 2)
        return frame

    def release(self):
        if self.face_landmarker is not None:
            self.face_landmarker.close()
            self.face_landmarker = None
