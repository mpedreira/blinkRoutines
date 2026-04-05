"""
Tests for detect_person endpoint — mocked Blink, Rekognition and Telegram.
"""
# pylint: disable=E0401
import pytest
from unittest.mock import MagicMock, patch
from app.api.api_v1.endpoints.detect_person import build_message, get_fresh_thumb
from app.classes.person_detector import UNKNOWN_PERSON


# ── build_message ─────────────────────────────────────────────────────────────

def test_build_message_no_faces():
    msg = build_message("Entrada", "2026-04-05 10:00:00", [])
    assert "No se detectaron" in msg
    assert "Entrada" in msg


def test_build_message_known_person():
    faces = [{'name': 'Manuel', 'confidence': 98.5}]
    msg = build_message("Entrada", "2026-04-05 10:00:00", faces)
    assert "Manuel" in msg


def test_build_message_unknown_person():
    faces = [{'name': UNKNOWN_PERSON, 'confidence': 0}]
    msg = build_message("Entrada", "2026-04-05 10:00:00", faces)
    assert "Persona desconocida" in msg


def test_build_message_deduplicates_same_person():
    """Same person detected twice → appear once with highest confidence."""
    faces = [
        {'name': 'Manuel', 'confidence': 98.0},
        {'name': 'Manuel', 'confidence': 75.0},
    ]
    msg = build_message("Entrada", "2026-04-05 10:00:00", faces)
    assert msg.count("Manuel") == 1


def test_build_message_low_confidence_treated_as_unknown():
    faces = [{'name': 'Manuel', 'confidence': 50.0}]
    msg = build_message("Entrada", "2026-04-05 10:00:00", faces)
    assert "Persona desconocida" in msg


# ── get_fresh_thumb ───────────────────────────────────────────────────────────

def _make_blink(camera_id="566211", cam_type="cam", thumbnail="/path/thumb"):
    blink = MagicMock()
    key = 'cameras' if cam_type == 'cam' else 'owls'
    blink.get_home_screen_info.return_value = {
        'response': {
            key: [{'id': int(camera_id), 'thumbnail': thumbnail}]
        }
    }
    return blink


def test_get_fresh_thumb_returns_path_for_cam():
    blink = _make_blink(cam_type="cam", thumbnail="/snap/cam.jpg")
    with patch('app.api.api_v1.endpoints.detect_person.sleep'):
        result = get_fresh_thumb(blink, "566211", "cam")
    assert result == "/snap/cam.jpg"
    blink.set_thumbnail.assert_called_once_with("566211")


def test_get_fresh_thumb_returns_path_for_owl():
    blink = _make_blink(cam_type="owl", thumbnail="/snap/owl.jpg")
    with patch('app.api.api_v1.endpoints.detect_person.sleep'):
        result = get_fresh_thumb(blink, "566211", "owl")
    assert result == "/snap/owl.jpg"
    blink.set_owl_thumbnail.assert_called_once_with("566211")


def test_get_fresh_thumb_returns_empty_when_camera_not_found():
    blink = MagicMock()
    blink.get_home_screen_info.return_value = {'response': {'cameras': []}}
    with patch('app.api.api_v1.endpoints.detect_person.sleep'):
        result = get_fresh_thumb(blink, "999999", "cam")
    assert result == ""
