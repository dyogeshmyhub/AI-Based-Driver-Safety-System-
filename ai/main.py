from __future__ import annotations

import os
import sys
import time
from datetime import datetime, timezone

import cv2

if __package__ in (None, ""):
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

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


def main() -> int:
    camera = Camera()
    detector = FaceDetector(max_faces=1)
    eye_detector = EyeDetector()
    blink_detector = BlinkDetector()
    drowsiness_detector = DrowsinessDetector()
    yawn_detector = YawnDetector()
    head_pose_estimator = HeadPoseEstimator()
    attention_detector = AttentionDetector()
    safety_engine = SafetyEngine()
    alert_manager = AlertManager()
    alarm = Alarm()
    session_manager = SessionManager()
    event_logger = EventLogger()
    session = session_manager.start_session()
    repository = session_manager.repository
    previous_risk = "LOW"
    previous_attention = "ATTENTIVE"
    previous_drowsiness = "ALERT"
    alert_count = 0
    drowsiness_events = 0
    last_yawn_count = 0
    last_safety = {"safety_score": 100, "risk_level": "LOW", "active_risks": [], "drowsiness_level": "ALERT"}

    def record_event(event_type: str, severity: str, message: str, payload: dict) -> None:
        event = event_logger.log_event(
            event_type=event_type,
            severity=severity,
            safety_score=int(payload["safety_score"]),
            risk_level=str(payload["risk_level"]),
            message=message,
            session_id=session.id,
            metadata={"active_risks": payload.get("active_risks", [])},
        )
        repository.save_event(SafetyEventRecord(
            id=event.event_id,
            session_id=session.id,
            timestamp=event.timestamp,
            event_type=event.event_type,
            severity=event.severity,
            safety_score=event.safety_score,
            risk_level=event.risk_level,
            message=event.message,
            metadata=event.metadata,
        ))

    try:
        if not camera.initialize():
            print(camera.last_error)
            return 1
        previous_time = time.time()
        while True:
            frame = camera.read_frame()
            if frame is None:
                print("Camera frame could not be read.")
                break
            frame = cv2.flip(frame, 1)
            detection = detector.process_frame(frame)
            left_ear = right_ear = average_ear = 0.0
            eye_status = "OPEN"
            eye_closed_duration = 0.0
            drowsiness_state = "ALERT"
            mouth_state = "MOUTH CLOSED"
            yawn_count = last_yawn_count
            yawn_detected = False
            yawn_duration = 0.0
            head_direction = "FORWARD"
            attention_state = "ATTENTIVE"
            risk_level = str(last_safety["risk_level"])
            safety_score = int(last_safety["safety_score"])
            active_risks = list(last_safety["active_risks"])
            face_status = "NOT DETECTED"

            if detection.face_detected:
                frame = detector.draw_face_box(frame, detection.landmarks)
                frame = detector.draw_landmarks(frame, detection.landmarks)
                face_landmarks = detection.landmarks[0]
                left_eye, right_eye = eye_detector.extract_eye_landmarks(face_landmarks, frame.shape)
                left_ear = calculate_ear(left_eye)
                right_ear = calculate_ear(right_eye)
                average_ear = (left_ear + right_ear) / 2.0
                frame = eye_detector.draw_eye_landmarks(frame, face_landmarks)
                timestamp = time.monotonic()
                eye_status = blink_detector.update(average_ear, timestamp)
                eye_closed_duration = blink_detector.eye_closed_duration
                drowsiness_state = drowsiness_detector.update(
                    average_ear=average_ear,
                    eye_closed_duration=eye_closed_duration,
                )["state"]

                mouth_points = []
                for index in (78, 81, 191, 80, 13, 14, 15, 16):
                    try:
                        landmark = face_landmarks[index]
                        mouth_points.append((landmark.x, landmark.y))
                    except (AttributeError, IndexError, TypeError):
                        pass
                if len(mouth_points) >= 2:
                    mouth_width = abs(mouth_points[0][0] - mouth_points[1][0])
                    mouth_height = abs(mouth_points[2][1] - mouth_points[4][1])
                    mouth_ratio = mouth_height / mouth_width if mouth_width > 0 else 0.0
                    yawn_payload = yawn_detector.update(mouth_ratio, timestamp)
                    mouth_state = yawn_payload["mouth_state"]
                    yawn_count = yawn_payload["yawn_count"]
                    yawn_detected = yawn_payload["yawn_detected"]
                    yawn_duration = yawn_payload["yawn_duration"]

                face_keypoints = {
                    "nose": (face_landmarks[1].x, face_landmarks[1].y),
                    "left_eye": (face_landmarks[33].x, face_landmarks[33].y),
                    "right_eye": (face_landmarks[263].x, face_landmarks[263].y),
                    "left_ear": (face_landmarks[234].x, face_landmarks[234].y),
                    "right_ear": (face_landmarks[454].x, face_landmarks[454].y),
                }
                pose = head_pose_estimator.estimate(face_keypoints)
                head_direction = pose["direction"]
                attention_state = attention_detector.update(
                    face_visible=True,
                    head_direction=head_direction,
                    eye_state=eye_status,
                    timestamp=timestamp,
                )["state"]
                last_safety = safety_engine.update(
                    average_ear=average_ear,
                    eye_state=eye_status,
                    blink_count=blink_detector.blink_count,
                    eye_closed_duration=eye_closed_duration,
                    yawn_count=yawn_count,
                    yawn_detected=yawn_detected,
                    yawn_duration=yawn_duration,
                    head_direction=head_direction,
                    yaw=pose["yaw"],
                    pitch=pose["pitch"],
                    roll=pose["roll"],
                    attention_state=attention_state,
                )
                drowsiness_state = str(last_safety["drowsiness_level"])
                risk_level = str(last_safety["risk_level"])
                safety_score = int(last_safety["safety_score"])
                active_risks = list(last_safety["active_risks"])
                face_status = "DETECTED"
            elif detection.faces_count > 1:
                face_status = "MULTIPLE"
            else:
                blink_detector.reset()
                drowsiness_detector.reset()
                yawn_detector.reset()
                attention_detector.reset()
                head_pose_estimator._history.clear()
                cv2.putText(frame, detection.message, (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

            alert_level, alert_message, alert_emitted = alert_manager.update(risk_level, drowsiness_state)
            if alert_emitted and alert_level != "INFO":
                alert_count += 1
                record_event("ALERT_TRIGGERED", alert_level, alert_message, last_safety)
                if alert_level == "CRITICAL":
                    alarm.play_critical()
                elif alert_level == "DANGER":
                    alarm.play_danger()
                else:
                    alarm.play_warning()
            elif alert_level == "INFO":
                alarm.stop_alarm()

            if risk_level != previous_risk:
                record_event("RISK_LEVEL_CHANGED", risk_level, f"Risk changed to {risk_level}", last_safety)
            if attention_state != previous_attention:
                event_type = "DRIVER_DISTRACTED" if attention_state == "DISTRACTED" else "DRIVER_ATTENTIVE"
                record_event(event_type, risk_level, f"Driver is {attention_state.lower()}", last_safety)
            if drowsiness_state != previous_drowsiness and drowsiness_state != "ALERT":
                drowsiness_events += 1
                event_type = "DROWSINESS_CRITICAL" if drowsiness_state == "CRITICAL" else "DROWSINESS_DETECTED"
                record_event(event_type, drowsiness_state, f"Drowsiness state: {drowsiness_state}", last_safety)
            if yawn_count > last_yawn_count:
                record_event("YAWN_DETECTED", "WARNING", "Yawn detected", last_safety)

            previous_risk = risk_level
            previous_attention = attention_state
            previous_drowsiness = drowsiness_state
            last_yawn_count = yawn_count
            session_manager.update_stats(
                safety_score=safety_score,
                risk_level=risk_level,
                alert_count=alert_count,
                drowsiness_events=drowsiness_events,
                yawns=yawn_count,
                blinks=blink_detector.blink_count,
            )

            current_time = time.time()
            fps = 1.0 / max((current_time - previous_time), 0.0001)
            previous_time = current_time
            duration = (datetime.now(timezone.utc) - datetime.fromisoformat(session.start_time)).total_seconds()
            minutes, seconds = divmod(int(duration), 60)
            hours, minutes = divmod(minutes, 60)
            active_risk_text = ", ".join(active_risks) if active_risks else "NONE"
            overlay = [
                ("DRIVER SAFETY AI", 25, (255, 255, 255)),
                ("Camera: ONLINE", 45, (0, 255, 0)),
                (f"MediaPipe: {'OK' if detector.mp_available else 'UNAVAILABLE'}", 65, (0, 255, 0)),
                ("Frame: OK", 85, (0, 255, 0)),
                (f"Resolution: {frame.shape[1]} x {frame.shape[0]}", 105, (255, 255, 255)),
                (f"Face: {face_status}", 125, (255, 255, 255)),
                (f"Faces: {detection.faces_count}", 145, (255, 255, 255)),
                (f"LEFT EAR: {left_ear:.2f}", 165, (255, 255, 255)),
                (f"RIGHT EAR: {right_ear:.2f}", 190, (255, 255, 255)),
                (f"AVERAGE EAR: {average_ear:.3f}", 215, (255, 255, 255)),
                (f"Eyes: {eye_status}", 240, (255, 255, 255)),
                (f"Blink Count: {blink_detector.blink_count}", 265, (255, 255, 255)),
                (f"Mouth: {mouth_state}", 290, (255, 255, 255)),
                (f"Yawn Count: {yawn_count}", 315, (255, 255, 255)),
                (f"Head: {head_direction}", 365, (255, 255, 255)),
                (f"Attention: {attention_state}", 390, (255, 255, 255)),
                (f"Drowsiness: {drowsiness_state}", 415, (255, 255, 255)),
                (f"Risk Level: {risk_level}", 440, (255, 255, 255)),
                (f"FPS: {int(fps)}", 465, (255, 255, 255)),
            ]
            for text, y_position, color in overlay:
                cv2.putText(frame, text, (20, y_position), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            phase5_overlay = [
                (f"Safety Score: {safety_score} / 100", 25, (255, 255, 255)),
                (f"Risk: {risk_level}", 50, (255, 255, 255)),
                (f"Active Risk: {active_risk_text[:26]}", 75, (0, 165, 255) if active_risks else (255, 255, 255)),
                (f"Alert: {'NORMAL' if alert_level == 'INFO' else alert_level}", 100, (0, 255, 255)),
                (f"Alarm: {'ACTIVE' if alarm.is_active() else 'OFF'}", 125, (0, 0, 255) if alarm.is_active() else (255, 255, 255)),
                (f"Session: ACTIVE {hours:02d}:{minutes:02d}:{seconds:02d}", 150, (0, 255, 0)),
                (f"Alerts: {alert_count}", 175, (255, 255, 255)),
            ]
            for text, y_position, color in phase5_overlay:
                cv2.putText(frame, text, (350, y_position), cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)
            cv2.imshow("Driver Safety AI", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            if key == ord("r"):
                camera.release()
                if not camera.initialize():
                    print(camera.last_error)
                    break
                previous_time = time.time()
    except KeyboardInterrupt:
        print("Stopping driver safety monitoring...")
    finally:
        alarm.stop_alarm()
        camera.release()
        detector.release()
        cv2.destroyAllWindows()
        session_manager.stop_session()
        repository.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
