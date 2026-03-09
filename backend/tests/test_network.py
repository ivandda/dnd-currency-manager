"""Tests for LAN URL detection endpoint."""


def test_lan_url_prefers_env_ip(client, monkeypatch):
    monkeypatch.setenv("LAN_IP", "192.168.1.42")

    response = client.get("/api/network/lan-url")
    data = response.json()

    assert response.status_code == 200
    assert data["ip"] == "192.168.1.42"
    assert data["source"] == "env"
    assert data["lan_url"].endswith(":3000")


def test_lan_url_uses_host_header_ip_when_available(client, monkeypatch):
    monkeypatch.delenv("LAN_IP", raising=False)

    response = client.get(
        "/api/network/lan-url",
        headers={"host": "192.168.1.50:8000"},
    )
    data = response.json()

    assert response.status_code == 200
    assert data["ip"] == "192.168.1.50"
    assert data["source"] == "host_header"
    assert data["lan_url"].startswith("http://192.168.1.50")


def test_lan_url_ignores_localhost_in_host_header(client, monkeypatch):
    monkeypatch.delenv("LAN_IP", raising=False)
    monkeypatch.setattr("app.main.os.path.exists", lambda _: True)

    response = client.get(
        "/api/network/lan-url",
        headers={"host": "localhost:8000"},
    )
    data = response.json()

    assert response.status_code == 200
    assert data["ip"] is None
    assert data["lan_url"] is None
    assert data["source"] == "none"
