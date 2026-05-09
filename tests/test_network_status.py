"""Tests for Blink network status parsing."""
# pylint: disable=E0401

from app.classes.adapters.blink_api import BlinkAPI


def test_extract_network_enabled_from_boolean_field():
    """A direct boolean field should be returned as-is."""
    enabled, source = BlinkAPI._extract_network_enabled_state({'armed': True})
    assert enabled is True
    assert source == 'armed'


def test_extract_network_enabled_from_string_field():
    """A textual state should be normalized into a boolean."""
    enabled, source = BlinkAPI._extract_network_enabled_state({'status': 'disarmed'})
    assert enabled is False
    assert source == 'status'


def test_extract_network_enabled_from_nested_state():
    """Nested state objects should also be supported."""
    enabled, source = BlinkAPI._extract_network_enabled_state({
        'state': {'status': 'armed'}
    })
    assert enabled is True
    assert source == 'state.status'


def test_extract_network_enabled_returns_none_when_missing():
    """Unknown payload shapes should not guess a value."""
    enabled, source = BlinkAPI._extract_network_enabled_state({'name': 'Casa'})
    assert enabled is None
    assert source is None