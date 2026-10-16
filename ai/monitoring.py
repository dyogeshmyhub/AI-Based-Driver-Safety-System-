from __future__ import annotations

import threading
import time
from datetime import datetime, timezone
from typing import Any

import cv2

from ai.alarm import Alarm
from ai.alert_manager import AlertManager
from ai.attention_detector import AttentionDetector
from ai.camera import Camera
from ai.blink_detector import BlinkDetector
from ai.drowsiness_detector import DrowsinessDetector
from ai.ear_calculator import calculate_ear
from ai.event_logger import EventLogger
from ai.eye_detector import EyeDetector
from ai.face_detector import FaceDetector
from ai.head_pose import HeadPoseEstimator
from ai.safety_engine import SafetyEngine
from ai.session_manager import SessionManager
from ai.yawn_detector import YawnDetector
from database.models import SafetyEventRecord


class DriverSafetyMonitor:
    """Threaded, headless adapter around the existing AI detection pipeline."""

    def __init__(self) -> None:
        self.camera = Camera()
        self.face_detector = FaceDetector(max_faces=1)
        self.eye_detector = EyeDetector()
        self.blink_detector = BlinkDetector()
        self.drowsiness_detector = DrowsinessDetector()
        self.yawn_detector = YawnDetector()
        self.head_pose = HeadPoseEstimator()
        self.attention_detector = AttentionDetector()
        self.safety_engine = SafetyEngine()
        self.alert_manager = AlertManager()
        self.alarm = Alarm()
        self.session_manager = SessionManager()
        self.event_logger = EventLogger()
        self._state_lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._last_frame = None
        self._session = None
        self._previous_risk = "LOW"
        self._previous_attention = "ATTENTIVE"
        self._previous_drowsiness = "ALERT"
        self._last_yawn_count = 0
        self._alert_count = 0
        self._drowsiness_events = 0
        self._last_tick = time.monotonic()
        self._state: dict[str, Any] = self._initial_state()

    @staticmethod
    def _initial_state() -> dict[str, Any]:
        return {
            "connected": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "monitoring": False,
            "camera": {"online": False, "status": "offline", "width": 0, "height": 0, "resolution": "0x0", "fps": 0},
            "face": {"detected": False, "faces": 0},
            "eyes": {"left_ear": 0.0, "right_ear": 0.0, "average_ear": 0.0, "status": "OPEN", "blink_count": 0},
            "mouth": {"status": "CLOSED", "yawn_count": 0},
            "head": {"direction": "FORWARD"},
            "attention": {"status": "ATTENTIVE"},
            "drowsiness": {"status": "ALERT"},
            "driver": {
                "face_detected": False,
                "faces": 0,
                "eyes": "OPEN",
                "left_ear": 0.0,
                "right_ear": 0.0,
                "average_ear": 0.0,
                "blink_count": 0,
                "mouth": "CLOSED",
                "yawn_count": 0,
                "head_pose": "FORWARD",
                "attention": "ATTENTIVE",
                "drowsiness": "ALERT",
            },
            "safety": {"score": 100, "risk_level": "LOW", "status": "SAFE", "active_risks": []},
            "alert": {"level": "INFO", "message": "Monitoring is stopped.", "alarm_active": False},
            "session": {"active": False, "duration_seconds": 0, "alerts": 0, "average_score": 100.0, "minimum_score": 100.0, "drowsiness_events": 0, "yawns": 0},
            "error": None,
        }

    def start(self) -> bool:
        with self._state_lock:
            if self.is_running:
                return False
            if self.face_detector.face_landmarker is None:
                self.face_detector = FaceDetector(max_faces=1)
            self.session_manager.reset()
            self._previous_risk = "LOW"
            self._previous_attention = "ATTENTIVE"
            self._previous_drowsiness = "ALERT"
            self._last_yawn_count = 0
            self._alert_count = 0
            self._drowsiness_events = 0
            self._last_tick = time.monotonic()
            if not self.camera.initialize():
                self._state["error"] = self.camera.last_error or "Camera unavailable."
                return False
            self._session = self.session_manager.start_session()
            self._stop_event.clear()
            self._state = self._initial_state()
            self._state["monitoring"] = True
            self._state["camera"] = {"status": "online", "resolution": "0x0", "fps": 0}
            self._thread = threading.Thread(target=self._run, name="driver-safety-ai", daemon=True)
            self._thread.start()
            return True

    def stop(self) -> bool:
        with self._state_lock:
            was_running = self.is_running
            self._stop_event.set()
            thread = self._thread
        if thread is not None and thread is not threading.current_thread():
            thread.join(timeout=5.0)
        self.alarm.stop_alarm()
        self.camera.release()
        self.face_detector.release()
        completed = self.session_manager.stop_session()
        self.session_manager.repository.close()
        with self._state_lock:
            self._thread = None
            self._state["monitoring"] = False
            self._state["camera"]["status"] = "offline"
            self._state["alert"] = {"level": "INFO", "message": "Monitoring is stopped.", "alarm_active": False}
            self._state["session"]["active"] = False
            if completed is not None:
                self._state["session"].update({
                    "duration_seconds": int(completed.duration),
                    "average_score": completed.average_safety_score,
                    "minimum_score": completed.minimum_safety_score,
                    "alerts": completed.total_alerts,
                    "drowsiness_events": completed.total_drowsiness_events,
                    "yawns": completed.total_yawns,
                })
        return was_running

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def snapshot(self) -> dict[str, Any]:
        with self._state_lock:
            state = dict(self._state)
            state["camera"] = dict(self._state["camera"])
            state["face"] = dict(self._state["face"])
            state["eyes"] = dict(self._state["eyes"])
            state["mouth"] = dict(self._state["mouth"])
            state["head"] = dict(self._state["head"])
            state["attention"] = dict(self._state["attention"])
            state["drowsiness"] = dict(self._state["drowsiness"])
            state["safety"] = dict(self._state["safety"])
            state["alert"] = dict(self._state["alert"])
            state["session"] = dict(self._state["session"])
            state["driver"] = {
                "face_detected": bool(state["face"].get("detected", False)),
                "faces": int(state["face"].get("faces", 0)),
                "eyes": str(state["eyes"].get("status", "OPEN")),
                "left_ear": float(state["eyes"].get("left_ear", 0.0)),
                "right_ear": float(state["eyes"].get("right_ear", 0.0)),
                "average_ear": float(state["eyes"].get("average_ear", 0.0)),
                "blink_count": int(state["eyes"].get("blink_count", 0)),
                "mouth": str(state["mouth"].get("status", "CLOSED")),
                "yawn_count": int(state["mouth"].get("yawn_count", 0)),
                "head_pose": str(state["head"].get("direction", "FORWARD")),
                "attention": str(state["attention"].get("status", "ATTENTIVE")),
                "drowsiness": str(state["drowsiness"].get("status", "ALERT")),
            }
            if state.get("safety", {}).get("risk_level") in {"LOW", "MEDIUM"}:
                state["safety"]["status"] = "SAFE"
            elif state.get("safety", {}).get("risk_level") == "HIGH":
                state["safety"]["status"] = "WARNING"
            else:
                state["safety"]["status"] = "CRITICAL"
            state["connected"] = bool(state.get("monitoring", False) or state.get("camera", {}).get("status") in {"online", "error"})
            return state

    def get_camera_frame(self) -> bytes | None:
        with self._state_lock:
            frame = self._last_frame
        if frame is None:
            return None
        success, buffer = cv2.imencode(".jpg", frame)
        if not success:
            return None
        return buffer.tobytes()

    def _run(self) -> None:
        try:
            while not self._stop_event.is_set():
                frame = self.camera.read_frame()
                if frame is None:
                    self._set_error("Camera frame could not be read.")
                    break
                self.process_frame(frame)
        except Exception as exc:  # keep the API alive if the camera/model fails
            self._set_error(f"AI service failure: {exc}")
        finally:
            self.alarm.stop_alarm()
            self.camera.release()

    def _set_error(self, message: str) -> None:
        with self._state_lock:
            self._state["error"] = message
            self._state["camera"]["status"] = "error"

    def _record_event(self, event_type: str, severity: str, message: str, safety: dict[str, Any]) -> None:
        if self._session is None:
            return
        event = self.event_logger.log_event(
            event_type=event_type,
            severity=severity,
            safety_score=int(safety["safety_score"]),
            risk_level=str(safety["risk_level"]),
            message=message,
            session_id=self._session.id,
            metadata={"active_risks": safety.get("active_risks", [])},
        )
        self.session_manager.repository.save_event(SafetyEventRecord(
            id=event.event_id,
            session_id=self._session.id,
            timestamp=event.timestamp,
            event_type=event.event_type,
            severity=event.severity,
            safety_score=event.safety_score,
            risk_level=event.risk_level,
            message=event.message,
            metadata=event.metadata,
        ))

    def process_frame(self, raw_frame) -> None:
        frame = cv2.flip(raw_frame, 1)
        detection = self.face_detector.process_frame(frame)
        left_ear = right_ear = average_ear = 0.0
        eye_status = "OPEN"
        eye_closed_duration = 0.0
        drowsiness_status = "ALERT"
        mouth_status = "CLOSED"
        yawn_count = self._last_yawn_count
        yawn_detected = False
        head_direction = "FORWARD"
        attention_status = "ATTENTIVE"
        previous = self.snapshot()
        safety = previous["safety"] | {"safety_score": previous["safety"]["score"]}

        if detection.face_detected:
            landmarks = detection.landmarks[0]
            left_eye, right_eye = self.eye_detector.extract_eye_landmarks(landmarks, frame.shape)
            left_ear = calculate_ear(left_eye)
            right_ear = calculate_ear(right_eye)
            average_ear = (left_ear + right_ear) / 2.0
            timestamp = time.monotonic()
            eye_status = self.blink_detector.update(average_ear, timestamp)
            eye_closed_duration = self.blink_detector.eye_closed_duration
            mouth_points = []
            for index in (78, 81, 191, 80, 13, 14, 15, 16):
                try:
                    point = landmarks[index]
                    mouth_points.append((point.x, point.y))
                except (AttributeError, IndexError, TypeError):
                    pass
            if len(mouth_points) >= 2:
                width = abs(mouth_points[0][0] - mouth_points[1][0])
                height = abs(mouth_points[2][1] - mouth_points[4][1])
                payload = self.yawn_detector.update(height / width if width else 0.0, timestamp)
                mouth_status = payload["mouth_state"].replace("MOUTH ", "")
                yawn_count = payload["yawn_count"]
                yawn_detected = payload["yawn_detected"]
            keypoints = {
                "nose": (landmarks[1].x, landmarks[1].y),
                "left_eye": (landmarks[33].x, landmarks[33].y),
                "right_eye": (landmarks[263].x, landmarks[263].y),
                "left_ear": (landmarks[234].x, landmarks[234].y),
                "right_ear": (landmarks[454].x, landmarks[454].y),
            }
            pose = self.head_pose.estimate(keypoints)
            head_direction = pose["direction"]
            attention_status = self.attention_detector.update(True, head_direction, eye_status, timestamp)["state"]
            drowsiness_status = self.drowsiness_detector.update(average_ear, eye_closed_duration)["state"]
            safety = self.safety_engine.update(
                average_ear=average_ear,
                eye_state=eye_status,
                blink_count=self.blink_detector.blink_count,
                eye_closed_duration=eye_closed_duration,
                yawn_count=yawn_count,
                yawn_detected=yawn_detected,
                yawn_duration=0.0,
                head_direction=head_direction,
                yaw=pose["yaw"],
                pitch=pose["pitch"],
                roll=pose["roll"],
                attention_state=attention_status,
            )
            drowsiness_status = str(safety["drowsiness_level"])
        else:
            self.blink_detector.reset()
            self.drowsiness_detector.reset()
            self.yawn_detector.reset()
            self.attention_detector.reset()
            self.head_pose._history.clear()

        risk_level = str(safety.get("risk_level", previous["safety"]["risk_level"]))
        score = int(max(0, min(100, safety.get("safety_score", previous["safety"]["score"]))))
        active_risks = list(safety.get("active_risks", []))
        alert_level, alert_message, alert_emitted = self.alert_manager.update(risk_level, drowsiness_status)
        if alert_emitted and alert_level != "INFO":
            self._alert_count += 1
            self._record_event("ALERT_TRIGGERED", alert_level, alert_message, safety)
            if alert_level == "CRITICAL":
                self.alarm.play_critical()
            elif alert_level == "DANGER":
                self.alarm.play_danger()
            else:
                self.alarm.play_warning()
        elif alert_level == "INFO":
            self.alarm.stop_alarm()
        if risk_level != self._previous_risk:
            self._record_event("RISK_LEVEL_CHANGED", risk_level, f"Risk changed to {risk_level}", safety)
        if attention_status != self._previous_attention:
            event_type = "DRIVER_DISTRACTED" if attention_status == "DISTRACTED" else "DRIVER_ATTENTIVE"
            self._record_event(event_type, risk_level, f"Driver is {attention_status.lower()}", safety)
        if drowsiness_status != self._previous_drowsiness and drowsiness_status != "ALERT":
            self._drowsiness_events += 1
            event_type = "DROWSINESS_CRITICAL" if drowsiness_status == "CRITICAL" else "DROWSINESS_DETECTED"
            self._record_event(event_type, drowsiness_status, f"Drowsiness state: {drowsiness_status}", safety)
        if yawn_count > self._last_yawn_count:
            self._record_event("YAWN_DETECTED", "WARNING", "Yawn detected", safety)
        self._previous_risk = risk_level
        self._previous_attention = attention_status
        self._previous_drowsiness = drowsiness_status
        self._last_yawn_count = yawn_count
        self.session_manager.update_stats(
            safety_score=score,
            risk_level=risk_level,
            alert_count=self._alert_count,
            drowsiness_events=self._drowsiness_events,
            yawns=yawn_count,
            blinks=self.blink_detector.blink_count,
        )
        now = time.monotonic()
        fps = 1.0 / max(now - self._last_tick, 0.0001)
        self._last_tick = now
        session_data = self.session_manager.get_current_session()
        duration = 0
        if session_data:
            duration = int((datetime.now(timezone.utc) - datetime.fromisoformat(session_data.start_time)).total_seconds())
        with self._state_lock:
            self._last_frame = frame.copy()
            self._state.update({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "monitoring": True,
                "camera": {"online": True, "status": "online", "width": int(frame.shape[1]), "height": int(frame.shape[0]), "resolution": f"{frame.shape[1]}x{frame.shape[0]}", "fps": int(fps)},
                "face": {"detected": detection.face_detected, "faces": detection.faces_count},
                "eyes": {"left_ear": round(left_ear, 3), "right_ear": round(right_ear, 3), "average_ear": round(average_ear, 3), "status": eye_status, "blink_count": self.blink_detector.blink_count},
                "mouth": {"status": mouth_status, "yawn_count": yawn_count},
                "head": {"direction": head_direction},
                "attention": {"status": attention_status},
                "drowsiness": {"status": drowsiness_status},
                "driver": {
                    "face_detected": bool(detection.face_detected),
                    "faces": int(detection.faces_count),
                    "eyes": eye_status,
                    "left_ear": round(left_ear, 3),
                    "right_ear": round(right_ear, 3),
                    "average_ear": round(average_ear, 3),
                    "blink_count": self.blink_detector.blink_count,
                    "mouth": mouth_status,
                    "yawn_count": yawn_count,
                    "head_pose": head_direction,
                    "attention": attention_status,
                    "drowsiness": drowsiness_status,
                },
                "safety": {"score": score, "risk_level": risk_level, "status": "SAFE" if risk_level in {"LOW", "MEDIUM"} else "WARNING" if risk_level == "HIGH" else "CRITICAL", "active_risks": active_risks},
                "alert": {"level": alert_level, "message": alert_message, "alarm_active": self.alarm.is_active()},
                "session": {"active": True, "duration_seconds": duration, "alerts": self._alert_count, "average_score": session_data.average_safety_score if session_data else score, "minimum_score": session_data.minimum_safety_score if session_data else score, "drowsiness_events": self._drowsiness_events, "yawns": yawn_count},
                "error": None,
            })


_monitor = DriverSafetyMonitor()


def get_monitor() -> DriverSafetyMonitor:
    return _monitor
