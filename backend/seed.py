import asyncio
from datetime import datetime, timedelta
from sqlalchemy import select
from database import AsyncSessionLocal, init_db
from models import CollectionPoint, StorageTank, LogisticsFleet, Alert

COLLECTION_POINTS = [
    {"name": "Susurluk Merkez Toplama",    "lat": 40.1833, "lng": 28.1333, "address": "Susurluk, Balıkesir",       "status": "active"},
    {"name": "Bandırma Süt Toplama",        "lat": 40.3553, "lng": 27.9778, "address": "Bandırma, Balıkesir",       "status": "active"},
    {"name": "Karacabey Çiftlik Noktası",   "lat": 40.2167, "lng": 28.3500, "address": "Karacabey, Bursa",          "status": "active"},
    {"name": "Mustafakemalpaşa Kooperatif", "lat": 40.0333, "lng": 28.4000, "address": "Mustafakemalpaşa, Bursa",   "status": "collecting"},
    {"name": "Gönen Süt Kooperatifi",       "lat": 40.1000, "lng": 27.6500, "address": "Gönen, Balıkesir",          "status": "active"},
    {"name": "Manyas Toplama Noktası",      "lat": 40.0500, "lng": 27.9667, "address": "Manyas, Balıkesir",         "status": "active"},
]

TANKS = [
    {"name": "Tank-A1 Susurluk", "lat": 40.1850, "lng": 28.1340, "capacity": 50_000, "current_level": 32_000, "temperature": 4.2},
    {"name": "Tank-B1 Bandırma",  "lat": 40.3560, "lng": 27.9790, "capacity": 80_000, "current_level": 71_500, "temperature": 3.8},
    {"name": "Tank-C1 Karacabey", "lat": 40.2175, "lng": 28.3510, "capacity": 40_000, "current_level": 12_000, "temperature": 4.5},
    {"name": "Tank-D1 MKP",       "lat": 40.0340, "lng": 28.4010, "capacity": 35_000, "current_level": 28_000, "temperature": 4.1},
    {"name": "Tank-E1 Gönen",     "lat": 40.1010, "lng": 27.6510, "capacity": 30_000, "current_level":  8_500, "temperature": 5.2},
    {"name": "Tank-F1 Manyas",    "lat": 40.0510, "lng": 27.9677, "capacity": 25_000, "current_level": 19_000, "temperature": 3.9},
]

_now = datetime.utcnow()

FLEET = [
    {
        "vehicle_id": "SZL-001", "driver_name": "Mehmet Yılmaz",
        "status": "en_route",
        "current_lat": 40.2100, "current_lng": 28.0500,
        "speed": 65.0, "temperature": 4.0, "load_level": 2800, "capacity": 5000,
        "collection_started_at": _now - timedelta(hours=1, minutes=20),
    },
    {
        "vehicle_id": "SZL-002", "driver_name": "Ali Demir",
        "status": "collecting",
        "current_lat": 40.1833, "current_lng": 28.1333,
        "speed": 0.0, "temperature": 4.2, "load_level": 1200, "capacity": 5000,
        "collection_started_at": _now - timedelta(minutes=45),
    },
    {
        "vehicle_id": "SZL-003", "driver_name": "Hasan Kaya",
        "status": "idle",
        "current_lat": 40.3553, "current_lng": 27.9778,
        "speed": 0.0, "temperature": 3.8, "load_level": 0, "capacity": 5000,
        "collection_started_at": None,
    },
    {
        "vehicle_id": "SZL-004", "driver_name": "Mustafa Öztürk",
        "status": "en_route",
        "current_lat": 40.1500, "current_lng": 28.2000,
        "speed": 72.0, "temperature": 4.3, "load_level": 4100, "capacity": 5000,
        "collection_started_at": _now - timedelta(hours=2, minutes=10),
    },
]

ALERTS = [
    {
        "alert_type": "temperature",
        "severity": "medium",
        "message": "Tank-E1 Gönen sıcaklığı yükseliyor: 5.2°C",
        "entity_id": 5,
        "entity_type": "tank",
    },
    {
        "alert_type": "tank_overflow",
        "severity": "high",
        "message": "Tank-B1 Bandırma %89.4 dolulukta — neredeyse dolu",
        "entity_id": 2,
        "entity_type": "tank",
    },
]


async def seed() -> None:
    await init_db()
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(CollectionPoint))
        if result.scalars().first():
            print("Veritabanı zaten seed edilmiş.")
            return

        cp_objs: list[CollectionPoint] = []
        for cp_data in COLLECTION_POINTS:
            cp = CollectionPoint(**cp_data)
            db.add(cp)
            cp_objs.append(cp)
        await db.flush()

        for i, tank_data in enumerate(TANKS):
            db.add(StorageTank(**tank_data, collection_point_id=cp_objs[i].id))

        for fleet_data in FLEET:
            db.add(LogisticsFleet(**fleet_data))

        for alert_data in ALERTS:
            db.add(Alert(**alert_data))

        await db.commit()
        print("Veritabanı başarıyla seed edildi.")


if __name__ == "__main__":
    asyncio.run(seed())
