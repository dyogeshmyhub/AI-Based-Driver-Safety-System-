from __future__ import annotations

import os
import sys
import time

import cv2

if __package__ in (None, ""):
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

from ai.camera import Camera
from ai.face_detector import FaceDetector


def main() -> int:
    camera = Camera()
    detector = FaceDetector(max_faces=1)
    if not camera.initialize():
        print(camera.last_error)
        detector.release()
        return 1

    previous_time = time.time()
    last_status = None
    try:
        while True:
            frame = camera.read_frame()
            if frame is None:
                print("Frame: FAIL")
                break

            frame = cv2.flip(frame, 1)
            detection = detector.process_frame(frame)
            if detection.face_detected:
                status = "FACE DETECTED"
                detector.draw_face_box(frame, detection.landmarks)
                detector.draw_landmarks(frame, detection.landmarks)
            else:
                status = "NO FACE DETECTED"

            if status != last_status:
                print(status)
                last_status = status

            current_time = time.time()
            fps = 1.0 / max(current_time - previous_time, 0.0001)
            previous_time = current_time
            cv2.putText(frame, "DRIVER SAFETY AI", (20, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(frame, f"MediaPipe: {'OK' if detector.mp_available else 'UNAVAILABLE'}", (20, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            cv2.putText(frame, "Frame: OK", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            cv2.putText(frame, f"Resolution: {frame.shape[1]} x {frame.shape[0]}", (20, 105), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.putText(frame, status, (20, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0) if detection.face_detected else (0, 0, 255), 2)
            cv2.putText(frame, f"Faces: {detection.faces_count}", (20, 155), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.putText(frame, f"FPS: {int(fps)}", (20, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.imshow("Face Detection Diagnostic", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        camera.release()
        detector.release()
        cv2.destroyAllWindows()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())