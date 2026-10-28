import json

from fastapi.testclient import TestClient

import app as api_app


def test_regions_serve_only_requested_country(tmp_path, monkeypatch):
    monkeypatch.setattr(api_app, "REGIONS_DIR", tmp_path)
    country = tmp_path / "USA"
    country.mkdir()
    payload = {"type": "FeatureCollection", "features": []}
    (country / "regions.geojson").write_text(json.dumps(payload), encoding="utf-8")
    client = TestClient(api_app.app)
    response = client.get("/api/countries/usa/regions")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/geo+json"
    assert response.json() == payload
    assert client.get("/api/countries/CAN/regions").status_code == 404
    assert client.get("/api/countries/USA123/regions").status_code == 400
    assert client.get("/api/countries/..%5C/regions").status_code == 400
