from ai.head_pose import HeadPoseEstimator


def _face_landmarks():
    return {
        "nose": (0.50, 0.45),
        "left_eye": (0.42, 0.38),
        "right_eye": (0.58, 0.38),
        "mouth": (0.50, 0.60),
        "left_ear": (0.30, 0.50),
        "right_ear": (0.70, 0.50),
    }


def test_forward_direction():
    estimator = HeadPoseEstimator()
    result = estimator.estimate(_face_landmarks())
    assert result["direction"] == "FORWARD"
    assert result["attention"] is True


def test_left_direction():
    estimator = HeadPoseEstimator()
    landmarks = _face_landmarks()
    landmarks["left_ear"] = (0.25, 0.50)
    landmarks["right_ear"] = (0.60, 0.50)
    result = estimator.estimate(landmarks)
    assert result["direction"] == "LEFT"


def test_right_direction():
    estimator = HeadPoseEstimator()
    landmarks = _face_landmarks()
    landmarks["left_ear"] = (0.55, 0.50)
    landmarks["right_ear"] = (0.80, 0.50)
    result = estimator.estimate(landmarks)
    assert result["direction"] == "RIGHT"


def test_up_direction():
    estimator = HeadPoseEstimator()
    landmarks = _face_landmarks()
    landmarks["nose"] = (0.50, 0.25)
    result = estimator.estimate(landmarks)
    assert result["direction"] == "UP"


def test_down_direction():
    estimator = HeadPoseEstimator()
    landmarks = _face_landmarks()
    landmarks["nose"] = (0.50, 0.75)
    result = estimator.estimate(landmarks)
    assert result["direction"] == "DOWN"


def test_invalid_landmarks_return_safe_default():
    estimator = HeadPoseEstimator()
    assert estimator.estimate({})["direction"] == "FORWARD"
    assert estimator.estimate(None)["direction"] == "FORWARD"
