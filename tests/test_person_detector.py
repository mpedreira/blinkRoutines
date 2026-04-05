"""
Tests for PersonDetectorRekognition — mocked Rekognition client.
"""
# pylint: disable=E0401
import pytest
from unittest.mock import MagicMock, patch
from botocore.exceptions import ClientError
from app.classes.adapters.person_detector_rekognition import PersonDetectorRekognition
from app.classes.person_detector import UNKNOWN_PERSON


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_config():
    cfg = MagicMock()
    cfg.auth = {
        'aws_access_key_id': 'FAKE',
        'aws_secret_access_key': 'FAKE',
        'region_name': 'us-east-1',
    }
    return cfg


@pytest.fixture
def detector(mock_config):
    with patch('boto3.client') as mock_boto:
        mock_client = MagicMock()
        mock_boto.return_value = mock_client
        # Simulate collection already exists
        mock_client.create_collection.side_effect = ClientError(
            {'Error': {'Code': 'ResourceAlreadyExistsException'}}, 'CreateCollection'
        )
        d = PersonDetectorRekognition(mock_config)
        d.client = mock_client
        return d


# ── detect_faces ──────────────────────────────────────────────────────────────

def test_detect_faces_returns_empty_when_no_faces(detector):
    detector.client.detect_faces.return_value = {'FaceDetails': []}
    assert detector.detect_faces(b'img') == []


def test_detect_faces_returns_known_person(detector):
    detector.client.detect_faces.return_value = {'FaceDetails': [{}]}
    detector.client.search_faces_by_image.return_value = {
        'FaceMatches': [
            {'Face': {'ExternalImageId': 'Manuel', 'Confidence': 98.5}}
        ]
    }
    result = detector.detect_faces(b'img')
    assert result == [{'name': 'Manuel', 'confidence': 98.5}]


def test_detect_faces_returns_unknown_when_no_match(detector):
    detector.client.detect_faces.return_value = {'FaceDetails': [{}]}
    detector.client.search_faces_by_image.return_value = {'FaceMatches': []}
    result = detector.detect_faces(b'img')
    assert result == [{'name': UNKNOWN_PERSON, 'confidence': 0}]


def test_detect_faces_keeps_only_best_match_per_face(detector):
    """Siblings should not both appear for the same detected face."""
    detector.client.detect_faces.return_value = {'FaceDetails': [{}]}
    detector.client.search_faces_by_image.return_value = {
        'FaceMatches': [
            {'Face': {'ExternalImageId': 'Hijo',  'Confidence': 97.0}},
            {'Face': {'ExternalImageId': 'Hija',  'Confidence': 85.0}},
        ]
    }
    result = detector.detect_faces(b'img')
    assert len(result) == 1
    assert result[0]['name'] == 'Hijo'


def test_detect_faces_handles_rekognition_error(detector):
    detector.client.detect_faces.side_effect = ClientError(
        {'Error': {'Code': 'InvalidImageFormatException'}}, 'DetectFaces'
    )
    assert detector.detect_faces(b'bad') == []


def test_detect_faces_two_real_people(detector):
    """Two faces in frame → two separate results."""
    detector.client.detect_faces.return_value = {'FaceDetails': [{}, {}]}
    detector.client.search_faces_by_image.return_value = {
        'FaceMatches': [
            {'Face': {'ExternalImageId': 'Manuel', 'Confidence': 99.0}}
        ]
    }
    result = detector.detect_faces(b'img')
    assert len(result) == 2
    names = {r['name'] for r in result}
    assert 'Manuel' in names
    assert UNKNOWN_PERSON in names


# ── detect_vacuum ─────────────────────────────────────────────────────────────

def test_detect_vacuum_returns_true_when_electrical_device_present(detector):
    detector.client.detect_labels.return_value = {
        'Labels': [
            {'Name': 'Electrical Device', 'Confidence': 79.8},
            {'Name': 'Indoors',           'Confidence': 99.9},
        ]
    }
    assert detector.detect_vacuum(b'img') is True


def test_detect_vacuum_returns_true_when_switch_present(detector):
    detector.client.detect_labels.return_value = {
        'Labels': [
            {'Name': 'Switch',  'Confidence': 79.8},
            {'Name': 'Indoors', 'Confidence': 99.9},
        ]
    }
    assert detector.detect_vacuum(b'img') is True


def test_detect_vacuum_returns_false_without_vacuum_labels(detector):
    detector.client.detect_labels.return_value = {
        'Labels': [
            {'Name': 'Indoors', 'Confidence': 99.9},
            {'Name': 'Door',    'Confidence': 88.8},
            {'Name': 'Floor',   'Confidence': 55.9},
        ]
    }
    assert detector.detect_vacuum(b'img') is False


def test_detect_vacuum_returns_false_on_rekognition_error(detector):
    detector.client.detect_labels.side_effect = ClientError(
        {'Error': {'Code': 'InvalidImageFormatException'}}, 'DetectLabels'
    )
    assert detector.detect_vacuum(b'img') is False


# ── detect_vacuum confidence threshold ───────────────────────────────────────

def test_detect_vacuum_respects_min_confidence(detector):
    """Label below min_confidence should not be returned by Rekognition (mocked correctly)."""
    # Rekognition filters by MinConfidence server-side; we simulate it returning nothing
    detector.client.detect_labels.return_value = {'Labels': []}
    assert detector.detect_vacuum(b'img', min_confidence=70) is False
