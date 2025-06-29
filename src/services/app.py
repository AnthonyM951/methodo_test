from fastapi import FastAPI, HTTPException
import requests
import openmeteo_requests
import requests_cache
from retry_requests import retry
import os
from dotenv import load_dotenv
import statistics
import datetime
from pathlib import Path

load_dotenv(dotenv_path=Path(".env"))
api_key_weather = os.getenv("weather_api_key")
api_key_ninja = os.getenv("ninja_api_key")

def fetch_coordinates(city_name: str):
    url = f"https://api.api-ninjas.com/v1/geocoding?city={city_name}"
    headers = {"User-Agent": "my-weather-app/1.0", "X-Api-Key": api_key_ninja}
    try:
        response = requests.get(url, headers=headers, timeout=10)
    except requests.exceptions.RequestException:
        raise HTTPException(status_code=503, detail="Service unavailable. Please try again later.")
    response.raise_for_status()
    result = response.json()
    if len(result) == 0:
        raise HTTPException(status_code=404, detail="City not found")
    if result:
        if city_name.lower() in result[0]["name"].lower():
            latitude = float(result[0]["latitude"])
            longitude = float(result[0]["longitude"])
            return latitude, longitude
        else:
            raise HTTPException(status_code=404, detail="City not found")
    else:
        raise HTTPException(status_code=404, detail="City not found")

cached_http = requests_cache.CachedSession('.cache', expire_after=3600)
resilient_session = retry(cached_http, retries=5, backoff_factor=0.2)
meteo_client = openmeteo_requests.Client(session=resilient_session)

app = FastAPI()

@app.get("/")
def root_endpoint():
    return {"message": "Welcome to the API!, Hello World !"}

@app.get("/health")
def status_check():
    return {"status": "ok", "message": "API OK!"}

@app.get("/geocoding/{city}")
def resolve_coordinates(city: str):
    lng, lat = fetch_coordinates(city)
    return {
        "city": city,
        "longitude": lng,
        "latitude": lat
    }

@app.get("/weather/current/{city}")
def retrieve_current_temperature(city: str):
    lat, lon = fetch_coordinates(city)
    temps = []
    data_sources = []

    # open-meteo
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m",
            "temperature_unit": "celsius"
        }
        result = meteo_client.weather_api(url, params=params)
        temp = result[0].Current().Variables(0).Value()
        temps.append(temp)
        data_sources.append("Openmeteo")
    except Exception as e:
        print(f"Erreur Openmeteo: {e}")

    # weather_api
    try:
        url = f"https://api.weatherapi.com/v1/current.json?key={api_key_weather}&q={lat},{lon}&aqi=no"
        response_api = requests.get(url)
        response_api.raise_for_status()
        temp_from_api = response_api.json()['current']['temp_c']
        temps.append(temp_from_api)
        data_sources.append("WeatherAPI")
    except Exception as e:
        print(f"Erreur WeatherAPI: {e}")

    if not temps:
        raise HTTPException(status_code=503, detail="Aucune source météo disponible actuellement.")

    mean_temp = statistics.mean(temps)

    output = {
        "city": city,
        "latitude": lat,
        "longitude": lon,
        "temperature": {
            "current": mean_temp,
            "unit": "celsius"
        },
        "source": data_sources
    }
    return output

@app.get("/weather/forecast/{city}")
def retrieve_forecast_temperature(city: str):
    lat, lon = fetch_coordinates(city)
    temps = []
    data_sources = []

    # open-meteo
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=,temperature_2m&forecast_days=1"
        response_openmeteo = requests.get(url)
        forecast_openmeteo = response_openmeteo.json()['hourly']['temperature_2m']
        temps.append(forecast_openmeteo)
        data_sources.append("Openmeteo")
    except Exception as e:
        print(f"Erreur Openmeteo: {e}")

    # weather_api
    try:
        url = f"https://api.weatherapi.com/v1/forecast.json?key={api_key_weather}&q={lat},{lon}&aqi=no"
        forecast_api = requests.get(url)
        forecast_api.raise_for_status()
        hourly_data = forecast_api.json()['forecast']['forecastday'][0]['hour']
        forecast_temps = [h['temp_c'] for h in hourly_data]
        temps.append(forecast_temps)
        data_sources.append("WeatherAPI")
    except Exception as e:
        print(f"Erreur WeatherAPI: {e}")

    if not temps:
        raise HTTPException(status_code=503, detail="Aucune source météo disponible actuellement.")

    if len(temps) == 2 and len(temps[0]) == 24 and len(temps[1]) == 24:
        hourly_avg = [(temps[0][i] + temps[1][i]) / 2 for i in range(24)]
    else:
        hourly_avg = temps[0] if temps else []

    result = {
        "city": city,
        "latitude": lat,
        "longitude": lon,
        "temperature": {
            "forecast_today": hourly_avg,
            "unit": "celsius"
        },
        "source": data_sources
    }
    return result

@app.get("/weather/history/{city}")
def retrieve_yesterday_temperature(city: str):
    lat, lon = fetch_coordinates(city)
    temps = []
    data_sources = []
    previous_day = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()

    # open-meteo
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=,temperature_2m&start_date={previous_day}&end_date={previous_day}"
        history_response = requests.get(url)
        temp_history = history_response.json()['hourly']['temperature_2m']
        temps.append(temp_history)
        data_sources.append("Openmeteo")
    except Exception as e:
        print(f"Erreur Openmeteo: {e}")

    # weather_api
    try:
        url = f"https://api.weatherapi.com/v1/history.json?key={api_key_weather}&q={lat},{lon}&aqi=no&dt={previous_day}"
        weather_response = requests.get(url)
        weather_response.raise_for_status()
        hourly = weather_response.json()['forecast']['forecastday'][0]['hour']
        temp_yesterday = [h['temp_c'] for h in hourly]
        temps.append(temp_yesterday)
        data_sources.append("WeatherAPI")
    except Exception as e:
        print(f"Erreur WeatherAPI: {e}")

    if not temps:
        raise HTTPException(status_code=503, detail="Aucune source météo disponible actuellement.")

    if len(temps) == 2 and len(temps[0]) == 24 and len(temps[1]) == 24:
        hourly_avg = [(temps[0][i] + temps[1][i]) / 2 for i in range(24)]
    else:
        hourly_avg = temps[0] if temps else []

    result = {
        "city": city,
        "latitude": lat,
        "longitude": lon,
        "temperature": {
            "forecast_yesterday": hourly_avg,
            "unit": "celsius"
        },
        "source": data_sources
    }
    return result
