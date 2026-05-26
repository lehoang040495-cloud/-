"""
Weather Service - Free weather API integration
Uses open-meteo.com (no API key required)
"""
import logging
import httpx

logger = logging.getLogger(__name__)

WMO_CODES = {
    0: "晴", 1: "晴", 2: "多云", 3: "阴",
    45: "雾", 48: "雾凇",
    51: "小毛毛雨", 53: "毛毛雨", 55: "大毛毛雨",
    61: "小雨", 63: "中雨", 65: "大雨",
    71: "小雪", 73: "中雪", 75: "大雪",
    80: "阵雨", 81: "中阵雨", 82: "大阵雨",
    95: "雷暴", 96: "雷暴冰雹",
}

SUGGESTIONS = {
    "晴": "天气晴朗，适合游览！记得涂防晒霜和带水。",
    "多云": "天气舒适，非常适合游览。",
    "阴": "天阴微凉，建议带件薄外套。",
    "雾": "有雾，注意安全，部分景点可能视野不佳。",
    "小雨": "有小雨，建议带伞，注意防滑。",
    "中雨": "雨势较大，建议在室内景点游览。",
    "大雨": "大雨天气，建议暂缓户外游览，注意安全。",
    "小雪": "有雪，路面可能湿滑，注意保暖和安全。",
    "雷暴": "有雷暴天气，请勿在空旷地带停留，注意安全。",
}


class WeatherService:
    async def get_weather(self, latitude: float = 30.57, longitude: float = 104.07,
                          location_name: str = "景区") -> dict:
        """
        Get current weather from open-meteo (free, no API key).
        Default coordinates: central China area.
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    "https://api.open-meteo.com/v1/forecast",
                    params={
                        "latitude": latitude,
                        "longitude": longitude,
                        "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m",
                        "timezone": "auto",
                    }
                )
                resp.raise_for_status()
                data = resp.json()

            current = data.get("current", {})
            temp = current.get("temperature_2m", "N/A")
            humidity = current.get("relative_humidity_2m", "N/A")
            wind = current.get("wind_speed_10m", "N/A")
            code = current.get("weather_code", 0)

            description = WMO_CODES.get(code, "未知")
            suggestion = SUGGESTIONS.get(description, "祝您游览愉快！")

            return {
                "location": location_name,
                "temperature": f"{temp}°C",
                "description": description,
                "humidity": f"{humidity}%",
                "wind": f"{wind} km/h",
                "suggestion": suggestion,
            }

        except Exception as e:
            logger.error(f"Weather fetch failed: {e}")
            return {
                "location": location_name,
                "temperature": "N/A",
                "description": "获取失败",
                "humidity": "N/A",
                "wind": "N/A",
                "suggestion": "建议查看天气预报后出行。",
            }


weather_service = WeatherService()
