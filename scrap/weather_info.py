import time
from typing import Optional

import requests
from pymongo.database import Database
from sqlmodel import Session

from config.database import engine
from dao.city_curd import get_city
from dao.mongo_curd import insert_weather
from entity.weather_archive import WeatherArchive

base_url = "https://www.nmc.cn"


def get_weather_info(city_code: str, mongo_db: Optional[Database] = None):
    weather_url = base_url + "/rest/weather"
    stationid = city_code
    with (Session(engine)) as session:
        city_name = get_city(session, city_code)
        if city_name is None:
            return
        city_name = city_name.city
    now = int(time.time() * 1000)
    params = {
        "stationid": stationid,
        "_": now
    }
    resp = requests.get(weather_url, params=params)
    data = WeatherArchive(city=city_name, city_code=city_code, data=resp.json(), created_at=now)
    if mongo_db is not None:
        try:
            insert_weather(mongo_db, data)
        except Exception:
            pass
    return resp.json()
