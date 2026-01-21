from sqlmodel import Session, select

from entity.city_info import CityInfo


def add_province(session: Session, city_info: CityInfo) -> CityInfo:
    session.add(city_info)
    session.commit()
    session.refresh(city_info)
    return city_info


def bulk_insert_city(session: Session, city_info: list[CityInfo]):
    session.add_all(city_info)
    session.commit()


def get_city(session: Session, code: str) -> CityInfo | None:
    return session.exec(select(CityInfo).where(CityInfo.city_code == code)).first()


def get_city_by_name(session: Session, name: str) -> CityInfo | None:
    return session.exec(select(CityInfo).where(CityInfo.city == name)).first()
