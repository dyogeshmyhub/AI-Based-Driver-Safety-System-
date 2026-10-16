from __future__ import annotations

import time
from typing import Optional

import cv2

from ai.config import get_camera_config


class Camera:
    def __init__(self, camera_index: int | None = None, frame_width: int | None = None, frame_height: int | None = None):
        config = get_camera_config()
        self.camera_index = camera_index if camera_index is not None else config.camera_index
        self.frame_width = frame_width if frame_width is not None else config.frame_width
        self.frame_height = frame_height if frame_height is not None else config.frame_height
        self.capture: Optional[cv2.VideoCapture] = None
        self.last_error: str = ""
        self.is_running = False

    def initialize(self) -> bool:
        try:
            self.capture = cv2.VideoCapture(self.camera_index)
            if not self.capture.isOpened():
                self.last_error = (
                    "Camera could not be accessed.\n"
                    "Please check camera permissions and make sure another application is not using the camera."
                )
                self.is_running = False
                return False

            self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
            self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)
            self.capture.set(cv2.CAP_PROP_FPS, 30)
            self.is_running = True
            self.last_error = ""
            return True
        except Exception as exc:  # pragma: no cover - defensive runtime guard
            self.last_error = f"Camera initialization failed: {exc}"
            self.is_running = False
            return False

    def read_frame(self):
        if not self.capture or not self.is_running:
            return None

        try:
            success, frame = self.capture.read()
            if not success or frame is None:
                self.last_error = "Camera frame could not be captured."
                return None
            return frame
        except Exception as exc:  # pragma: no cover - defensive runtime guard
            self.last_error = f"Frame read failed: {exc}"
            return None

    def release(self):
        if self.capture is not None:
            self.capture.release()
        self.is_running = False
        self.capture = None

    def get_fps(self, prev_time: float) -> float:
        current_time = time.time()
        fps = 1.0 / max((current_time - prev_time), 0.0001)
        return fps
