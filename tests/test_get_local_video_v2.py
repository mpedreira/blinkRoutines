"""Tests for API v2 get_local_video endpoint."""
# pylint: disable=E0401

from fastapi.testclient import TestClient

from app.main import app


class _ConfigCameraMissing:
    def __init__(self):
        self.cameras = {}


class _ConfigNoClips:
    def __init__(self):
        self.cameras = {"Entrada": {"id": "123"}}


class _ConfigWithClip:
    def __init__(self):
        self.cameras = {"Entrada": {"id": "123"}}


class _BlinkNoClips:
    def __init__(self, _config):
        pass

    def __set_token__(self):
        return None

    def get_server(self):
        return "https://blink.example"

    def get_home_screen_info(self):
        return {
            "response": {
                "cameras": [{"id": 123, "network_id": 9}],
                "sync_modules": [{"id": 77, "network_id": 9}],
            }
        }

    def get_local_clips(self, _sync_module_id):
        return {"response": {"clips": []}}


class _BlinkWithClip(_BlinkNoClips):
    def get_local_clips(self, _sync_module_id):
        return {
            "response": {
                "clips": [{"id": "clip-1", "camera_name": "Entrada", "created_at": "2026-05-25 10:00:00"}],
                "network_id": "9",
                "sync_module_id": "77",
                "manifest_id": "11",
            }
        }

    def get_local_clip(self, _clips):
        return iter([b"ab", b"", b"cd"])


def test_get_local_video_v2_camera_not_found(monkeypatch):
    """Missing camera should return 400 JSON payload."""
    import app.api.api_v2.endpoints.get_local_video as endpoint_mod

    monkeypatch.setattr(endpoint_mod, "ConfigAWS", _ConfigCameraMissing)
    client = TestClient(app)

    response = client.get("/api/v2/get_local_video/Entrada")

    assert response.status_code == 400
    payload = response.json()
    assert payload["is_ok"] is False
    assert "not found" in payload["response"]


def test_get_local_video_v2_no_clips(monkeypatch):
    """When Blink has no local clips, endpoint should return 404 JSON."""
    import app.api.api_v2.endpoints.get_local_video as endpoint_mod

    monkeypatch.setattr(endpoint_mod, "ConfigAWS", _ConfigNoClips)
    monkeypatch.setattr(endpoint_mod, "BlinkAPI", _BlinkNoClips)
    client = TestClient(app)

    response = client.get("/api/v2/get_local_video/Entrada")

    assert response.status_code == 404
    payload = response.json()
    assert payload["is_ok"] is False
    assert payload["response"] == "No hay videos"


def test_get_local_video_v2_streams_video(monkeypatch):
    """When clip exists, endpoint should stream mp4 attachment."""
    import app.api.api_v2.endpoints.get_local_video as endpoint_mod

    monkeypatch.setattr(endpoint_mod, "ConfigAWS", _ConfigWithClip)
    monkeypatch.setattr(endpoint_mod, "BlinkAPI", _BlinkWithClip)
    client = TestClient(app)

    response = client.get("/api/v2/get_local_video/Entrada")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("video/mp4")
    assert "attachment; filename=" in response.headers["content-disposition"]
    assert response.content == b"abcd"
