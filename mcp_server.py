from mcp.server.fastmcp import FastMCP
import openmeteo_requests
import requests
from pydantic import Field
from tzlocal import get_localzone
import pandas as pd

mcp = FastMCP("WeatherMCP", log_level="ERROR")
openmeteo = openmeteo_requests.Client()

@mcp.tool(
    name = "get_location",
    description = "Get weather data for a location at a time"
)
def get_location(
    latitude:float = Field(description="Latitude of the location"),
    longitude: float = Field(description="Longitude of the location"),
    date: str = Field(description="Date in YYYY-MM-DD format")
):
    
    local_tz = str(get_localzone())
    params = {
        "latitude": latitude,    
        "longitude": longitude,
        "daily": "temperature_2m_max,windspeed_10m_max,precipitation_sum,uv_index_max",
        "timezone": local_tz
    }

    url = "https://api.open-meteo.com/v1/forecast"
    responses = openmeteo.weather_api(url, params=params)
    response = responses[0] 

    daily = response.Daily()

    dates = pd.date_range(
        start=pd.to_datetime(daily.Time(), unit="s", utc=True),
        end=pd.to_datetime(daily.TimeEnd(), unit="s", utc=True),
        freq=pd.Timedelta(seconds=daily.Interval()),
        inclusive="left"
    )
    date_index = dates.strftime("%Y-%m-%d").tolist().index(date)

    daily_temperature = daily.Variables(0).ValuesAsNumpy()
    daily_wind = daily.Variables(1).ValuesAsNumpy()
    daily_rain = daily.Variables(2).ValuesAsNumpy()
    daily_uv = daily.Variables(3).ValuesAsNumpy()

    return {
        "temperature": (daily_temperature[date_index] * 9/5) + 32,
        "wind_speed": daily_wind[date_index] * 0.621371,
        "precipitation": daily_rain[date_index] * 0.0393701,
        "uv_index": daily_uv[date_index]
    }
    
if __name__ == "__main__":
    mcp.run(transport="stdio")


#weather rating prompt