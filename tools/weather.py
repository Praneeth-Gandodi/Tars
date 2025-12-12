import requests


url = "https://api.open-meteo.com/v1/forecast"
place_url = "https://geocoding-api.open-meteo.com/v1/search"

def get_weather(place="Tirupati"):
    """
    Retrieve current weather information for a given place using the Open-Meteo
    Geocoding API and Forecast API. This function is designed for use in an MCP
    server environment where tools must return structured, machine-readable data.

    Args:
        place (str): The name of the city to fetch weather data for.

    Returns:
        dict: A dictionary containing the current weather values returned by
              Open-Meteo, including temperature, windspeed, weather code, and
              timestamp. Raises an error if the location cannot be resolved.
    """

    city_params = {
        "name": place,
        "count": 1
    }
    place_response = requests.get(place_url, params=city_params).json()
    lat = place_response["results"][0]["latitude"]
    lon = place_response["results"][0]["longitude"]
    params = {
        "latitude": lat,
        "longitude": lon,
        "current_weather": "true",
        "hourly": "temperature_2m,relative_humidity_2m"
    }
    response = requests.get(url, params=params)
    data = response.json()
    try:
        return data['current_weather']
    except Exception as e:
        return [f"Error occured {e}"]

