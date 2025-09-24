import asyncio
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("weather")

# Constants
NWS_API_BASE = "https://api.weather.gov"
USER_AGENT = "weather-app/1.0"


async def make_nws_request(url: str) -> dict[str, Any] | None:
    """Make a request to the NWS API with proper error handling."""
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/geo+json"
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None


def format_alert(feature: dict) -> str:
    """Format an alert feature into a readable string."""
    props = feature["properties"]
    return f"""
Event: {props.get('event', 'Unknown')}
Area: {props.get('areaDesc', 'Unknown')}
Severity: {props.get('severity', 'Unknown')}
Description: {props.get('description', 'No description available')}
Instructions: {props.get('instruction', 'No specific instructions provided')}
"""


@mcp.tool()
async def get_alerts(state: str) -> str:
    """Get weather alerts for a US state.

    Args:
        state: Two-letter US state code (e.g. CA, NY)
    """
    url = f"{NWS_API_BASE}/alerts/active/area/{state}"
    data = await make_nws_request(url)

    if not data or "features" not in data:
        return "Unable to fetch alerts or no alerts found."

    if not data["features"]:
        return "No active alerts for this state."

    alerts = [format_alert(feature) for feature in data["features"]]
    return "\n---\n".join(alerts)


@mcp.tool()
async def get_tokyo_weather() -> str:
    """Get weather forecast for Tokyo."""
    # ref: https://anko.education/webapi/jma
    url = "https://www.jma.go.jp/bosai/forecast/data/forecast/130000.json"
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            data = response.json()

        # JMAのレスポンスは配列。
        # timeSeries -> areas[].weathers の先頭が「今日」
        preferred_names = ("東京地方", "東京", "Tokyo")
        today_weather: str | None = None

        if isinstance(data, list):
            for obj in data:
                time_series = (
                    obj.get("timeSeries", [])
                    if isinstance(obj, dict)
                    else []
                )
                for ts in time_series:
                    areas = (
                        ts.get("areas", [])
                        if isinstance(ts, dict)
                        else []
                    )
                    for area in areas:
                        if not isinstance(area, dict):
                            continue
                        weathers_any = area.get("weathers")
                        if (
                            not isinstance(weathers_any, list)
                            or not weathers_any
                        ):
                            continue
                        weathers = weathers_any
                        area_info = (
                            area.get("area", {})
                            if isinstance(area.get("area"), dict)
                            else {}
                        )
                        area_name = area_info.get("name", "")
                        if any(name in area_name for name in preferred_names):
                            today_weather = weathers[0] if weathers else None
                            break
                    if today_weather:
                        break
                if today_weather:
                    break

        # フォールバック: 最初に見つかったweathersの先頭を使用
        if not today_weather and isinstance(data, list):
            for obj in data:
                time_series = (
                    obj.get("timeSeries", [])
                    if isinstance(obj, dict)
                    else []
                )
                for ts in time_series:
                    areas = (
                        ts.get("areas", [])
                        if isinstance(ts, dict)
                        else []
                    )
                    for area in areas:
                        if isinstance(area, dict):
                            weathers_any = area.get("weathers")
                            if (
                                isinstance(weathers_any, list)
                                and weathers_any
                            ):
                                today_weather = weathers_any[0]
                                break
                            break
                    if today_weather:
                        break
                if today_weather:
                    break

        if today_weather:
            return f"東京の今日の天気: {today_weather}"
        return "東京の天気情報を取得できませんでした。"
    except Exception:
        return "東京の天気情報を取得できませんでした。"


@mcp.tool()
async def get_forecast(latitude: float, longitude: float) -> str:
    """Get weather forecast for a location.

    Args:
        latitude: Latitude of the location
        longitude: Longitude of the location
    """
    # First get the forecast grid endpoint
    points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
    points_data = await make_nws_request(points_url)

    if not points_data:
        return "Unable to fetch forecast data for this location."

    # Get the forecast URL from the points response
    forecast_url = points_data["properties"]["forecast"]
    forecast_data = await make_nws_request(forecast_url)

    if not forecast_data:
        return "Unable to fetch detailed forecast."

    # Format the periods into a readable forecast
    periods = forecast_data["properties"]["periods"]
    forecasts = []
    for period in periods[:5]:  # Only show next 5 periods
        forecast = f"""
{period['name']}:
Temperature: {period['temperature']}°{period['temperatureUnit']}
Wind: {period['windSpeed']} {period['windDirection']}
Forecast: {period['detailedForecast']}
"""
        forecasts.append(forecast)

    return "\n---\n".join(forecasts)


async def main():
    # ロサンゼルス
    # result = await get_forecast(34.0522, -118.2437)
    result = await get_tokyo_weather()
    print(result)

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')
