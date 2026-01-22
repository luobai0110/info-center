import os
import time
from typing import Optional

import requests
from pymongo.database import Database
from sqlmodel import Session

from config.database import engine
from dao.city_curd import get_city
from dao.mongo_curd import insert_weather
from entity.weather_archive import WeatherArchive
from service.monitor.monitor import warning

base_url = "https://www.nmc.cn"
notice_url = os.getenv("HTTP_NOTICE_URL")


def get_weather_info(city_code: str, mongo_db: Optional[Database] = None):
    weather_url = base_url + "/rest/weather"
    stationid = city_code
    with (Session(engine)) as session:
        city_name = get_city(session, city_code)
        if city_name is None:
            warning("城市不存在" + city_code, "weather", to_="@doomer")
            return None
        city_name = city_name.city
    now = int(time.time() * 1000)
    params = {
        "stationid": stationid,
        "_": now
    }
    resp = requests.get(weather_url, params=params)
    if resp.status_code != 200:
        warning("获取天气数据失败" + resp.text, "weather", to_="@doomer")
        return None
    data = resp.json()
    if data['data'] is None:
        warning("天气数据为空" + data, "weather", to_="@doomer")
        return None
    data = WeatherArchive(city=city_name, city_code=city_code, data=resp.json())
    if mongo_db is not None:
        try:
            insert_weather(mongo_db, data)
        except Exception as e:
            warning(f"插入数据库失败", "weather", to_="@doomer")
            pass
    return resp.json()
