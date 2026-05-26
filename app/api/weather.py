"""
Weather API - Weather query for scenic area
"""
import logging
from fastapi import APIRouter, Query

from app.services.weather_service import weather_service
from app.schemas import WeatherResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["Weather"])


@router.get("/weather", response_model=WeatherResponse)
async def get_weather(
    latitude: float = Query(30.57, description="纬度"),
    longitude: float = Query(104.07, description="经度"),
    location: str = Query("景区", description="地点名称"),
):
    """Get current weather for the scenic area"""
    data = await weather_service.get_weather(latitude, longitude, location)
    return WeatherResponse(**data)
