import json

from app import config
from app.on_prem_fetcher import fetch_on_prem_data


def test_get_on_prem_server_url_prefers_env(monkeypatch):
    monkeypatch.setenv("ON_PREM_SERVER_IP", "192.168.1.25")
    monkeypatch.setenv("ON_PREM_SERVER_PORT", "9000")

    assert config.get_on_prem_server_url() == "http://192.168.1.25:9000"


def test_fetch_on_prem_data_uses_configured_server(monkeypatch):
    class FakeResponse:
        def __init__(self, payload):
            self.payload = payload

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return json.dumps(self.payload).encode("utf-8")

        def close(self):
            pass

    def fake_urlopen(request):
        assert request.full_url == "http://192.168.1.25:9000/api/data"
        return FakeResponse({"status": "ok", "items": [{"id": 1}]})

    monkeypatch.setenv("ON_PREM_SERVER_IP", "192.168.1.25")
    monkeypatch.setenv("ON_PREM_SERVER_PORT", "9000")
    monkeypatch.setenv("ON_PREM_DATA_ENDPOINT", "/api/data")
    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    assert fetch_on_prem_data() == {"status": "ok", "items": [{"id": 1}]}
