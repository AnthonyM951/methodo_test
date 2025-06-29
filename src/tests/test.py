import requests

BASE_URL = "http://127.0.0.1:8000"

def test_get_forecast_invalid_city():
    city = "invalid_city"
    res = requests.get(f"{BASE_URL}/weather/forecast/{city}")
    assert res.status_code == 404

def test_get_temperature_invalid_city():
    city = "invalid_city"
    res = requests.get(f"{BASE_URL}/weather/current/{city}")
    assert res.status_code == 404

def test_get_temperature_empty_city():
    city = ""
    res = requests.get(f"{BASE_URL}/weather/current/{city}")
    assert res.status_code == 404
    # assert "detail" in data
    # assert data["detail"] == "City not found"

def test_get_forecast():
    city = "Paris"
    res = requests.get(f"{BASE_URL}/weather/forecast/{city}")
    assert res.status_code == 200
    data = res.json()
    assert data["city"] == city
    assert len(data["temperature"]["forecast_today"]) == 24

def test_get_history_empty_city():
    city = ""
    res = requests.get(f"{BASE_URL}/weather/history/{city}")
    assert res.status_code == 404

def test_get_temperature():
    city = "Paris"
    res = requests.get(f"{BASE_URL}/weather/current/{city}")
    assert res.status_code == 200
    data = res.json()
    assert data["city"] == city
    assert "temperature" in data
    assert "current" in data["temperature"]
    assert "unit" in data["temperature"]

def test_get_history_invalid_city():
    city = "city_non_existent"
    res = requests.get(f"{BASE_URL}/weather/history/{city}")
    assert res.status_code == 404

def test_get_forecast_empty_city():
    city = ""
    res = requests.get(f"{BASE_URL}/weather/forecast/{city}")
    assert res.status_code == 404

def test_geocoding_access():
    res = requests.get(f"{BASE_URL}/geocoding/Paris")
    assert res.status_code == 200

def test_get_history():
    city = "Paris"
    res = requests.get(f"{BASE_URL}/weather/history/{city}")
    assert res.status_code == 200
    data = res.json()
    assert data["city"] == city
    assert len(data["temperature"]["forecast_yesterday"]) == 24
