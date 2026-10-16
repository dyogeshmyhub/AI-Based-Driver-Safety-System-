from ai.blink_detector import BlinkDetector


def test_open_closed_open_counts_single_blink():
    detector = BlinkDetector()
    detector.update(0.30)
    detector.update(0.10)
    detector.update(0.30)
    assert detector.blink_count == 1
    assert detector.is_blinking is False


def test_repeated_closed_frames_still_count_one_blink():
    detector = BlinkDetector()
    detector.update(0.30)
    detector.update(0.10)
    detector.update(0.10)
    detector.update(0.10)
    detector.update(0.30)
    assert detector.blink_count == 1


def test_open_frames_do_not_count_blinks():
    detector = BlinkDetector()
    detector.update(0.30)
    detector.update(0.30)
    detector.update(0.30)
    assert detector.blink_count == 0
