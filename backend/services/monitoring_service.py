from __future__ import annotations

from ai.monitoring import DriverSafetyMonitor, get_monitor


class MonitoringService:
    """Application-facing service for the single background AI monitor."""

    def __init__(self, monitor: DriverSafetyMonitor | None = None) -> None:
        self.monitor = monitor or get_monitor()

    def start(self) -> bool:
        return self.monitor.start()

    def stop(self) -> bool:
        return self.monitor.stop()

    def is_running(self) -> bool:
        return self.monitor.is_running

    def snapshot(self) -> dict:
        return self.monitor.snapshot()

    def get_camera_frame(self) -> bytes | None:
        return self.monitor.get_camera_frame()

    @property
    def repository(self):
        return self.monitor.session_manager.repository


monitoring_service = MonitoringService()
