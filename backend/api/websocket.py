from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.services.monitoring_service import monitoring_service

logger = logging.getLogger(__name__)
router = APIRouter()


def _serialize_state() -> dict:
    state = monitoring_service.snapshot()
    camera = state.get("camera", {})
    driver = state.get("driver", {})
    safety = state.get("safety", {})
    return {
        "type": "monitoring_update",
        "connected": bool(state.get("connected", True)),
        "monitoring": bool(state.get("monitoring", False)),
        "timestamp": state.get("timestamp"),
        "camera": {
            "online": bool(camera.get("online", camera.get("status") == "online")),
            "status": camera.get("status", "offline"),
            "width": int(camera.get("width", 0)),
            "height": int(camera.get("height", 0)),
            "resolution": camera.get("resolution", "0x0"),
            "fps": int(camera.get("fps", 0)),
        },
        "driver": {
            "face_detected": bool(driver.get("face_detected", state.get("face", {}).get("detected", False))),
            "faces": int(driver.get("faces", state.get("face", {}).get("faces", 0))),
            "eyes": driver.get("eyes", state.get("eyes", {}).get("status", "OPEN")),
            "left_ear": float(driver.get("left_ear", state.get("eyes", {}).get("left_ear", 0.0))),
            "right_ear": float(driver.get("right_ear", state.get("eyes", {}).get("right_ear", 0.0))),
            "average_ear": float(driver.get("average_ear", state.get("eyes", {}).get("average_ear", 0.0))),
            "blink_count": int(driver.get("blink_count", state.get("eyes", {}).get("blink_count", 0))),
            "mouth": driver.get("mouth", state.get("mouth", {}).get("status", "CLOSED")),
            "yawn_count": int(driver.get("yawn_count", state.get("mouth", {}).get("yawn_count", 0))),
            "head_pose": driver.get("head_pose", state.get("head", {}).get("direction", "FORWARD")),
            "attention": driver.get("attention", state.get("attention", {}).get("status", "ATTENTIVE")),
            "drowsiness": driver.get("drowsiness", state.get("drowsiness", {}).get("status", "ALERT")),
        },
        "safety": {
            "score": int(safety.get("score", state.get("safety", {}).get("score", 100))),
            "risk_level": safety.get("risk_level", state.get("safety", {}).get("risk_level", "LOW")),
            "status": safety.get("status", "SAFE" if safety.get("risk_level") in {"LOW", "MEDIUM"} else "WARNING"),
            "active_risks": list(safety.get("active_risks", state.get("safety", {}).get("active_risks", []))),
        },
        "alert": state.get("alert", {"level": "INFO", "message": "Monitoring is stopped.", "alarm_active": False}),
        "session": state.get("session", {"active": False, "duration_seconds": 0}),
        "error": state.get("error"),
    }


@router.websocket("/ws/monitoring")
async def monitor_websocket(websocket: WebSocket) -> None:
    await websocket.accept()
    logger.info("WebSocket connection established")
    try:
        while True:
            await websocket.send_json(_serialize_state())
            await asyncio.sleep(0.25)
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception:
        logger.exception("WebSocket monitoring failure")
        try:
            await websocket.close()
        except Exception:
            pass


@router.websocket("/ws/monitor")
async def legacy_monitor_websocket(websocket: WebSocket) -> None:
    await monitor_websocket(websocket)
