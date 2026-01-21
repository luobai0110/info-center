from typing import Any, Dict, Optional

from pymongo import ASCENDING, DESCENDING
from pymongo.collection import Collection
from pymongo.database import Database

from entity.weather_archive import WeatherArchive
from bson import ObjectId


def ensure_weather_indexes(db: Database):
    col = db.get_collection("weather_archive")
    col.create_index([("city_code", ASCENDING)], name="idx_city_code")
    col.create_index([("created_at", DESCENDING)], name="idx_created_at")
    return col


def insert_weather(db: Database, data: WeatherArchive) -> Any:
    col = ensure_weather_indexes(db)
    doc: Dict[str, Any] = data.model_dump(exclude_none=True)
    if "id" in doc:
        try:
            doc["_id"] = ObjectId(doc.pop("id"))
        except Exception:
            doc.pop("id", None)
    return col.insert_one(doc).inserted_id


def upsert_weather_by_city_code(db: Database, data: WeatherArchive) -> Dict[str, Any]:
    col = ensure_weather_indexes(db)
    doc: Dict[str, Any] = data.model_dump(exclude_none=True)
    if "id" in doc:
        try:
            doc["_id"] = ObjectId(doc.pop("id"))
        except Exception:
            doc.pop("id", None)
    result = col.update_one({"city_code": data.city_code}, {"$set": doc}, upsert=True)
    return {"matched": result.matched_count, "modified": result.modified_count, "upserted_id": str(result.upserted_id) if result.upserted_id else None}


def get_latest_by_city_code(db: Database, city_code: str) -> Optional[Dict[str, Any]]:
    col: Collection = ensure_weather_indexes(db)
    return col.find_one({"city_code": city_code}, sort=[("created_at", -1)])


def list_by_city_code(db: Database, city_code: str, limit: int = 50) -> list[Dict[str, Any]]:
    col: Collection = ensure_weather_indexes(db)
    cursor = col.find({"city_code": city_code}).sort("created_at", DESCENDING).limit(limit)
    return list(cursor)


def delete_by_city_code(db: Database, city_code: str) -> int:
    col: Collection = ensure_weather_indexes(db)
    return col.delete_many({"city_code": city_code}).deleted_count
