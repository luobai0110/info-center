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


def clean_weather_data(data):
    INVALID_VALUES = {9999, 9999.0, "9999"}
    INVALID_KEYS = {"url", "radar"}
    # dict：递归清理键值
    if isinstance(data, dict):
        result = {}
        for k, v in data.items():
            # 1. 按 key 直接删除
            if k in INVALID_KEYS:
                continue
            # 只有在「基础类型」时才做 INVALID 判断
            if not isinstance(v, (dict, list)) and v in INVALID_VALUES:
                continue
            cleaned_v = clean_weather_data(v)
            # 子结构被清空时不保留
            if cleaned_v in (None, {}, []):
                continue
            result[k] = cleaned_v
        return result
    # list：递归清理元素
    if isinstance(data, list):
        result = []
        for item in data:
            if not isinstance(item, (dict, list)) and item in INVALID_VALUES:
                continue
            cleaned_item = clean_weather_data(item)
            if cleaned_item in (None, {}, []):
                continue
            result.append(cleaned_item)
        return result
    # 基础类型直接返回
    return data


def clean_future_weather_info(data):
    # 只保留 real (实时天气) 和 air (空气质量)
    keep_keys = {"real", "air"}
    return {k: data[k] for k in keep_keys if k in data}


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

    cleaned_data = clean_weather_data(data)

    data = WeatherArchive(city=city_name, city_code=city_code, created_at=now, data=cleaned_data['data'])
    if mongo_db is not None:
        try:
            insert_weather(mongo_db, data)
        except Exception as e:
            warning("插入数据库失败", "weather", to_="@doomer")
            pass
    return cleaned_data['data']
