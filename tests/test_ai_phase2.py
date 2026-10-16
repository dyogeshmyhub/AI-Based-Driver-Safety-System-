from ai.camera import Camera
from ai.face_detector import FaceDetector, FaceDetectionResult


def test_camera_configuration_defaults():
    camera = Camera()
    assert camera.camera_index == 0
    assert camera.frame_width == 640
    assert camera.frame_height == 480


def test_face_detector_initialization():
    detector = FaceDetector()
    assert detector is not None
    assert detector.max_faces == 1
    assert hasattr(detector, 'process_frame')


def test_camera_handles_invalid_index_gracefully(monkeypatch):
    class FakeCapture:
        def __init__(self, *args, **kwargs):
            pass

        def isOpened(self):
            return False

        def release(self):
            pass

    monkeypatch.setattr("cv2.VideoCapture", lambda *args, **kwargs: FakeCapture())
    camera = Camera(camera_index=999)
    assert camera.initialize() is False
    assert "Camera could not be accessed" in camera.last_error


def test_face_detection_result_has_expected_structure():
    result = FaceDetectionResult(
        face_detected=False,
        faces_count=0,
        landmarks=[],
        message="NO DRIVER FACE DETECTED",
    )
    assert isinstance(result, FaceDetectionResult)
    assert result.face_detected is False
    assert result.faces_count == 0
    assert result.message == "NO DRIVER FACE DETECTED"
