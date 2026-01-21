from typing import Any, Dict

from pydantic import BaseModel

class WeatherArchive(BaseModel):
    id: str | None = None
    city: str
    city_code: str
    data: Dict[str, Any]
    created_at: int | None = None

