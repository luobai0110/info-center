from sqlmodel import SQLModel, Field


class CityInfo(SQLModel, table=True):
    __tablename__ = "city_info"
    id: int | None = Field(default=None, primary_key=True)
    province: str
    province_code: str
    city: str  # 城市名称
    city_code: str
    url: str
