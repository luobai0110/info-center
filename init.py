import requests
from sqlalchemy import text
from sqlmodel import Session

from config.database import engine
from dao.city_curd import bulk_insert_city
from entity.city_info import CityInfo

base_url = "https://www.nmc.cn/rest/province"


def init_city_info():
    all_province_url = base_url + "/all"
    resp = requests.post(all_province_url)
    province = []
    if resp.status_code == 200:
        values = resp.json()
        print(values)
        for value in values:
            cities = requests.post(base_url + "/" + value['code'])
            for city in cities.json():
                print(city)
                province.append(CityInfo(city_code=city['code'], province=value['name'], province_code=value['code'],
                                         city=city['city'], url=city['url']))
    with Session(engine) as session:
        session.exec(
            text("TRUNCATE TABLE city_info RESTART IDENTITY CASCADE;")
        )
        session.commit()
        bulk_insert_city(session, province)
