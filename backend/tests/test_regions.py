import json

import pytest



def test_regions_serve_only_requested_country(client, tmp_path, monkeypatch, application):
    monkeypatch.setattr(application.state.settings, "regions_dir", tmp_path)
    country = tmp_path / "USA"
    country.mkdir()
    payload = {"type": "FeatureCollection", "features": []}
    (country / "regions.geojson").write_text(json.dumps(payload), encoding="utf-8")
    response = client.get("/api/countries/usa/regions")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/geo+json"
    assert response.json() == payload
    assert client.get("/api/countries/CAN/regions").status_code == 404
    assert client.get("/api/countries/USA123/regions").status_code == 400
    assert client.get("/api/countries/..%5C/regions").status_code == 400


def test_countries_serves_geojson(client, tmp_path, monkeypatch, application):
    countries_file = tmp_path / "countries.geojson"
    payload = {"type": "FeatureCollection", "features": [{
        "type": "Feature", "properties": {"name": "Demo", "iso_a3": "AAA"},
        "geometry": None,
    }]}
    countries_file.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setattr(application.state.settings, "countries_file", countries_file)
    response = client.get("/api/countries")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/geo+json"
    assert response.json() == payload


def test_missing_countries_returns_service_unavailable(client, tmp_path, monkeypatch, application):
    monkeypatch.setattr(application.state.settings, "countries_file", tmp_path / "missing.geojson")
    response = client.get("/api/countries")
    assert response.status_code == 503
    assert response.json() == {"detail": "Countries data not available"}


def test_missing_country_regions_returns_not_found(client, tmp_path, monkeypatch, application):
    monkeypatch.setattr(application.state.settings, "regions_dir", tmp_path)
    response = client.get("/api/countries/CAN/regions")
    assert response.status_code == 404
    assert response.json() == {"detail": "Regions data not available for this country"}


@pytest.mark.parametrize("code", ["US", "USA1", "123", "..%5C", "%C3%85BC"])
def test_invalid_country_code_returns_bad_request(client, code):
    response = client.get(f"/api/countries/{code}/regions")
    assert response.status_code == 400
    assert response.json() == {"detail": "Expected a three-letter country code"}
