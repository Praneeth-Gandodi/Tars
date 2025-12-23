import requests
import pytz
from datetime import datetime
from rich.console import Console

console = Console()

def get_dt_by_place(place:str):
    """
    Gets the date and time of the place / city that is passed
    Args:
        city (str): Name of the place that you want to know time and date details  for.

    Returns:
        str: A string mentioning the time and date.
    """
    place_url = "https://geocoding-api.open-meteo.com/v1/search"
    city_params = {
        "name": place,
        "count": 1
        }
    place_response = requests.get(place_url, params=city_params).json()
    time_zone = place_response["results"][0]["timezone"]
    
    try:
        time_f = pytz.timezone(time_zone)
        time = datetime.now(time_f)
    except Exception as e:
        console.print(e)
    
    return f"The current time in {place} is {time.strftime("%I:%M:%S:%p")} and date is {time.strftime("%d:%m:%Y")}"

def get_datetime():
    """
    Get current date and time - NO PARAMETERS NEEDED
    The function will always returns the current time.
    """
    now = datetime.now()
    return {
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%I:%M:%S"),
        "timezone": now.strftime("%Z") or "Local",
        "day": now.strftime("%A")
    }
