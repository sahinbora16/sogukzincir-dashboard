# SoğukZincir Lojistik Dashboard — Proje Kuralları

## Teknoloji Kısıtlamaları
- Backend: SADECE Python 3.11 + FastAPI 0.111 + SQLAlchemy 2.0 (async)
- Frontend: SADECE React 18 + TypeScript 5 + Tailwind CSS 3
- State: Zustand (Redux, MobX veya Context API KULLANMA)
- Harita: Leaflet.js (Mapbox, Google Maps KULLANMA)
- ORM: SQLAlchemy async (raw SQL veya başka ORM KULLANMA)
- Task queue: Celery + Redis (threading veya multiprocessing KULLANMA)

## İş Mantığı Kuralları
- Soğuk zincir: Araç sıcaklığı +2 °C altına veya +6 °C üstüne çıkarsa
  ANINDA Alerts tablosuna kayıt ekle ve WebSocket broadcast yap
- Bozulma indeksi: Bk = t * exp(0.1 * T) formülünü utils.py içinde tut,
  başka yerde hesaplama
- Bk > 8.0 veya T > 6.0 → alert_type = "HIGH_RISK"
- Bk > 4.0 → alert_type = "MEDIUM_RISK"

## Kodlama Standartları
- Tüm async fonksiyonlar için type hints zorunlu
- Pydantic v2 schema'ları schemas.py'de, SQLAlchemy modelleri models.py'de
- Frontend bileşenleri PascalCase, hooks camelCase ile başlar (use...)
- Tailwind renkler: mavi (#0f4c81) ve yeşil (#1a7a4a) SoğukZincir Lojistik kurumsal renkleri
- Hiçbir API anahtarı veya şifre .env dışında yer almaz

## Test Kuralları
- Backend: pytest + pytest-asyncio; her endpoint için en az bir test
- Frontend: Vitest; her Zustand store action için test
- Yeni özellik eklerken önce test yaz (TDD)

## Yapılmayacaklar
- Docker dışında global pip install yapma
- SQLite kullanma (sadece PostgreSQL)
- console.log production kodunda kalmasın
- any tipi TypeScript'te kullanma
