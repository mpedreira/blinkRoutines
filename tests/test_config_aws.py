"""
Tests for ConfigAWS — no AWS credentials required.
"""
# pylint: disable=C0301,E0401
import json
import random
import string
import pytest
from unittest.mock import patch, mock_open
from app.classes.adapters.config_aws import ConfigAWS


# ── Helpers ───────────────────────────────────────────────────────────────────

def _rand_token(n=10):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=n))


MINIMAL_CONFIG = json.dumps({
    "blink_tier": "e007",
    "blink_account_id": "145137",
    "blink_token_auth": "tok",
    "blink_refresh_token": "ref",
    "blink_client_id": "",
    "blink_hardware_id": "BlinkCamera_test",
    "blink_user": "test@test.com",
    "blink_password": "pass",
    "telegram_api_token": "telegram:token",
    "cameras": {"Entrada": {"id": "566211", "type": "cam"}},
    "aws_access_key_id": "",
    "aws_secret_access_key": "",
    "aws_region": "us-east-1",
    "aws_bucket": "",
    "aws_folder": "",
    "aws_table": "",
})


@pytest.fixture
def cfg(tmp_path, monkeypatch):
    """ConfigAWS backed by a temp file, no real disk side-effects."""
    cfg_file = tmp_path / "config.ini"
    cfg_file.write_text(MINIMAL_CONFIG)
    import app.classes.adapters.config_aws as mod
    monkeypatch.setattr(mod, "CONFIGFILE", str(cfg_file))
    return ConfigAWS()


# ── Tests: basic init ─────────────────────────────────────────────────────────

def test_blink_endpoint_uses_tier(cfg):
    assert cfg.endpoints['BLINK'] == "https://rest-e007.immedia-semi.com"


def test_cameras_parsed_as_dict(cfg):
    assert isinstance(cfg.cameras, dict)
    assert "Entrada" in cfg.cameras


def test_account_id_loaded(cfg):
    assert cfg.session['ACCOUNT_ID'] == "145137"


# ── Tests: update_token_auth ──────────────────────────────────────────────────

def test_update_token_auth_saves_access_token(cfg):
    token = _rand_token()
    cfg.update_token_auth({'access_token': token})
    assert cfg.session['TOKEN_AUTH'] == token


def test_update_token_auth_saves_refresh_token(cfg):
    token, refresh = _rand_token(), _rand_token(20)
    cfg.update_token_auth({'access_token': token, 'refresh_token': refresh})
    assert cfg.session['REFRESH_TOKEN'] == refresh


def test_update_token_auth_saves_client_id(cfg):
    token = _rand_token()
    cfg.update_token_auth({'access_token': token, 'client_id': '99999'})
    assert cfg.session['CLIENT_ID'] == '99999'


def test_update_token_auth_ignores_missing_client_id(cfg):
    """client_id absent in response must not overwrite existing value."""
    cfg.session['CLIENT_ID'] = 'existing'
    cfg.update_token_auth({'access_token': _rand_token()})
    assert cfg.session['CLIENT_ID'] == 'existing'


def test_update_token_auth_returns_true(cfg):
    assert cfg.update_token_auth({'access_token': _rand_token()}) is True


# ── Tests: update_tier_info ───────────────────────────────────────────────────

def test_update_tier_info_updates_tier(cfg):
    cfg.update_tier_info('prod', None)
    assert cfg.session['TIER'] == 'prod'


def test_update_tier_info_updates_account_id(cfg):
    cfg.update_tier_info(None, '999999')
    assert cfg.session['ACCOUNT_ID'] == '999999'


def test_update_tier_info_ignores_none_values(cfg):
    original_tier = cfg.session['TIER']
    cfg.update_tier_info(None, None)
    assert cfg.session['TIER'] == original_tier


# ── Tests: oauth state round-trip ─────────────────────────────────────────────

def test_oauth_state_round_trip(cfg):
    cfg.save_oauth_state('verifier123', 'csrf456', {'cookie': 'val'})
    state = cfg.load_oauth_state()
    assert state['code_verifier'] == 'verifier123'
    assert state['csrf_token'] == 'csrf456'
    assert state['cookies'] == {'cookie': 'val'}


def test_load_oauth_state_returns_empty_cookies_if_missing(cfg):
    state = cfg.load_oauth_state()
    assert state['cookies'] == {}
