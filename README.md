# SoğukZincir Lojistik Dashboard

Süt toplama filolarını ve soğuk zincir depolama tanklarını gerçek zamanlı izleyen full-stack lojistik yönetim sistemi.

![Tech Stack](https://img.shields.io/badge/FastAPI-0.136-009688?style=flat&logo=fastapi)
![React](https://img.shields.io/badge/React-18-61DAFB?style=flat&logo=react)
![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?style=flat&logo=typescript)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=flat&logo=postgresql)

## Özellikler

- **Gerçek zamanlı filo takibi** — WebSocket üzerinden araç konum ve sıcaklık güncellemeleri
- **Soğuk zincir alarmı** — Araç sıcaklığı +2 °C altına veya +6 °C üstüne çıkınca anında uyarı
- **Bozulma indeksi** — `Bk = t × exp(0.1 × T)` formülüyle süt kalitesi tahmini
- **Tank seviye izleme** — 6 depolama tankı için kapasite göstergeleri
- **Leaflet.js harita** — Susurluk/Bandırma bölgesinde 6 toplama noktası
- **KPI paneli** — Aktif araç sayısı, toplam süt hacmi, kritik alarm özeti

## Teknoloji Yığını

| Katman | Teknoloji |
|---|---|
| Backend | Python 3.11 · FastAPI · SQLAlchemy 2.0 async |
| Veritabanı | PostgreSQL 16 (geliştirme: SQLite) |
| Frontend | React 18 · TypeScript 5 · Tailwind CSS 3 |
| State | Zustand |
| Harita | Leaflet.js / react-leaflet |
| Altyapı | Docker Compose · Redis |
| Test | pytest · pytest-asyncio · Vitest |

## Kurulum

### Docker ile (önerilen)

```bash
# 1. Repo'yu klonla
git clone https://github.com/sahinbora16/sogukzincir-dashboard.git
cd sogukzincir-dashboard

# 2. Ortam değişkenlerini ayarla
cp .env.example .env
# .env dosyasını aç ve DB_PASSWORD değerini düzenle

# 3. Başlat
docker compose up --build
```

Uygulama adresleri:
- Dashboard → http://localhost:5173
- API Docs (Swagger) → http://localhost:8000/docs

### Yerel geliştirme (Docker olmadan)

```bash
# Backend
cd backend
cp .env.example .env          # DATABASE_URL=sqlite+aiosqlite:///./sogukzincir.db
pip install -r requirements.txt
python seed.py                 # Örnek veriyi yükle
python -m uvicorn main:app --reload --port 8000

# Frontend (yeni terminal)
cd frontend
cp .env.example .env
npm install
npm run dev
```

## Proje Yapısı

```
sogukzincir-dashboard/
├── backend/
│   ├── main.py            # FastAPI uygulaması, WebSocket yöneticisi
│   ├── models.py          # SQLAlchemy ORM modelleri
│   ├── schemas.py         # Pydantic v2 şemaları
│   ├── utils.py           # Bk formülü ve alarm yardımcıları
│   ├── seed.py            # Örnek veri yükleyici
│   ├── routers/
│   │   ├── fleet.py       # POST /fleet/{id}/telemetry + WebSocket
│   │   ├── tanks.py       # Tank CRUD
│   │   └── alerts.py      # Alarm listeleme ve çözümleme
│   └── tests/
│       └── test_fleet_telemetry.py
├── frontend/
│   └── src/
│       ├── components/    # KpiCard, TankGauge, FleetMap, AlertPanel
│       ├── hooks/         # usePolling, useFleetSocket, useMarkers
│       ├── pages/         # Dashboard
│       ├── store/         # Zustand store
│       └── types/         # TypeScript tipleri + Bk hesaplama
├── docker-compose.yml
└── .env.example
```

## API Referansı

| Method | Endpoint | Açıklama |
|---|---|---|
| GET | `/fleet` | Tüm araçları listele |
| POST | `/fleet/{id}/telemetry` | GPS + sıcaklık güncelle, alarm değerlendir |
| GET | `/tanks` | Tüm tankları listele |
| GET | `/alerts` | Aktif alarmlari listele |
| PATCH | `/alerts/{id}/resolve` | Alarmı çözümlendi olarak işaretle |
| WS | `/ws/fleet` | Gerçek zamanlı filo olayları |

## Testleri Çalıştırma

```bash
cd backend
pip install -r requirements-test.txt
pytest -v
```

## İş Mantığı

**Soğuk Zincir Kuralları:**
- Kabul edilen sıcaklık aralığı: **+2 °C — +6 °C**
- Aralık dışına çıkıldığında → `HIGH_RISK` alarmı + WebSocket broadcast

**Bozulma İndeksi (Bk):**
```
Bk = t × exp(0.1 × T)
```
- `t` : Toplama başlangıcından bu yana geçen süre (saat)
- `T` : Araç iç sıcaklığı (°C)
- `Bk > 8.0` → HIGH_RISK
- `Bk > 4.0` → MEDIUM_RISK
