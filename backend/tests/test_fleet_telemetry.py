"""
TDD — tests written before the POST /{id}/telemetry endpoint exists.

Endpoint contract:
  POST /api/fleet/{id}/telemetry
  Body: { gps_lat, gps_lng, current_temp_c, speed?, load_level?, status? }
  → 200  güncellenmiş araç
  → 422  geçersiz payload
  → 404  bilinmeyen araç

Side-effects (background task evaluate_and_alert):
  T > 6°C veya T < 2°C → HIGH_RISK  (cold-chain ihlali)
  Bk > 8.0             → HIGH_RISK  (spoilage — cold ihlali yoksa)
  Bk > 4.0             → MEDIUM_RISK
  safe                 → alert yok
"""

import pytest
from datetime import datetime, timedelta


# ── HTTP contract ─────────────────────────────────────────────────────────────

class TestPostTelemetryContract:
    async def test_returns_200_and_updates_position(
        self, client, seeded_vehicle
    ) -> None:
        payload = {
            "gps_lat": 40.2100,
            "gps_lng": 28.0500,
            "current_temp_c": 4.5,
            "speed": 65.0,
        }
        resp = await client.post(
            f"/api/fleet/{seeded_vehicle.id}/telemetry", json=payload
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["current_lat"] == pytest.approx(40.2100)
        assert body["current_lng"] == pytest.approx(28.0500)
        assert body["temperature"] == pytest.approx(4.5)
        assert body["speed"] == pytest.approx(65.0)

    async def test_returns_404_for_unknown_vehicle(self, client) -> None:
        payload = {"gps_lat": 40.0, "gps_lng": 28.0, "current_temp_c": 4.0}
        resp = await client.post("/api/fleet/99999/telemetry", json=payload)
        assert resp.status_code == 404

    async def test_returns_422_for_missing_required_fields(
        self, client, seeded_vehicle
    ) -> None:
        resp = await client.post(
            f"/api/fleet/{seeded_vehicle.id}/telemetry",
            json={"gps_lat": 40.0},  # gps_lng ve current_temp_c eksik
        )
        assert resp.status_code == 422

    async def test_optional_fields_are_truly_optional(
        self, client, seeded_vehicle
    ) -> None:
        payload = {"gps_lat": 40.1, "gps_lng": 28.1, "current_temp_c": 5.0}
        resp = await client.post(
            f"/api/fleet/{seeded_vehicle.id}/telemetry", json=payload
        )
        assert resp.status_code == 200

    async def test_status_collecting_sets_collection_started_at(
        self, client, seeded_vehicle
    ) -> None:
        payload = {
            "gps_lat": 40.1,
            "gps_lng": 28.1,
            "current_temp_c": 4.0,
            "status": "collecting",
        }
        resp = await client.post(
            f"/api/fleet/{seeded_vehicle.id}/telemetry", json=payload
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "collecting"
        assert body["collection_started_at"] is not None

    async def test_status_idle_clears_collection_started_at(
        self, client, seeded_vehicle
    ) -> None:
        # Önce collecting yap
        await client.post(
            f"/api/fleet/{seeded_vehicle.id}/telemetry",
            json={"gps_lat": 40.1, "gps_lng": 28.1, "current_temp_c": 4.0, "status": "collecting"},
        )
        # Sonra idle'a al
        resp = await client.post(
            f"/api/fleet/{seeded_vehicle.id}/telemetry",
            json={"gps_lat": 40.1, "gps_lng": 28.1, "current_temp_c": 4.0, "status": "idle"},
        )
        assert resp.status_code == 200
        assert resp.json()["collection_started_at"] is None


# ── evaluate_and_alert — unit tests ──────────────────────────────────────────

class FakeSession:
    def __init__(self) -> None:
        self.added: list = []

    def add(self, obj) -> None:
        self.added.append(obj)

    async def commit(self) -> None:
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        pass


class FakeWsManager:
    def __init__(self) -> None:
        self.broadcasts: list[dict] = []

    async def broadcast(self, msg: dict) -> None:
        self.broadcasts.append(msg)


class TestEvaluateAndAlert:
    async def test_high_risk_when_temp_above_cold_chain_max(self) -> None:
        from routers.fleet import evaluate_and_alert
        from models import Alert

        session = FakeSession()
        ws = FakeWsManager()
        await evaluate_and_alert(1, 9.0, ws, db_factory=lambda: session)

        assert any(
            isinstance(a, Alert) and a.alert_type == "HIGH_RISK"
            for a in session.added
        )
        assert any(m["type"] == "alert" for m in ws.broadcasts)

    async def test_high_risk_when_temp_below_cold_chain_min(self) -> None:
        from routers.fleet import evaluate_and_alert
        from models import Alert

        session = FakeSession()
        ws = FakeWsManager()
        await evaluate_and_alert(1, 1.0, ws, db_factory=lambda: session)

        assert any(
            isinstance(a, Alert) and a.alert_type == "HIGH_RISK"
            for a in session.added
        )

    async def test_medium_risk_when_bk_between_4_and_8_safe_temp(self) -> None:
        """
        T=4°C (soğuk zincir ihlali yok), t=3h:
        Bk = 3 * exp(0.4) ≈ 4.47  →  MEDIUM_RISK
        """
        from routers.fleet import evaluate_and_alert
        from models import Alert

        session = FakeSession()
        ws = FakeWsManager()
        # t_hours = 3h → collection_started_at = 3 saat önce
        collection_started_at = datetime.utcnow() - timedelta(hours=3)
        await evaluate_and_alert(
            1, 4.0, ws,
            collection_started_at=collection_started_at,
            db_factory=lambda: session,
        )

        alert_types = [a.alert_type for a in session.added if hasattr(a, "alert_type")]
        assert "MEDIUM_RISK" in alert_types

    async def test_no_alert_for_safe_temp_and_low_bk(self) -> None:
        """T=4°C, t=1h → Bk = 1*exp(0.4) ≈ 1.49 → alert yok."""
        from routers.fleet import evaluate_and_alert

        session = FakeSession()
        ws = FakeWsManager()
        collection_started_at = datetime.utcnow() - timedelta(hours=1)
        await evaluate_and_alert(
            1, 4.0, ws,
            collection_started_at=collection_started_at,
            db_factory=lambda: session,
        )

        assert session.added == []
        assert ws.broadcasts == []

    async def test_cold_chain_breach_prevents_duplicate_high_risk(self) -> None:
        """
        T=9°C tetikler: cold_chain HIGH_RISK.
        Bk de eşiği aşar ama cold ihlali varsa ikinci HIGH_RISK eklenmemeli.
        """
        from routers.fleet import evaluate_and_alert
        from models import Alert

        session = FakeSession()
        ws = FakeWsManager()
        collection_started_at = datetime.utcnow() - timedelta(hours=5)
        await evaluate_and_alert(
            1, 9.0, ws,
            collection_started_at=collection_started_at,
            db_factory=lambda: session,
        )

        high_risk_count = sum(
            1 for a in session.added
            if isinstance(a, Alert) and a.alert_type == "HIGH_RISK"
        )
        assert high_risk_count == 1, "Tek bir HIGH_RISK alert bekleniyor"


# ── Integration: cold-chain ihlali /api/alerts'te görünmeli ──────────────────

class TestColdChainIntegration:
    async def test_breach_creates_high_risk_alert_in_db(
        self, client, seeded_vehicle
    ) -> None:
        payload = {"gps_lat": 40.0, "gps_lng": 28.0, "current_temp_c": 8.5}
        await client.post(
            f"/api/fleet/{seeded_vehicle.id}/telemetry", json=payload
        )

        alerts_resp = await client.get("/api/alerts/")
        matching = [
            a for a in alerts_resp.json()
            if a["alert_type"] == "HIGH_RISK" and a["entity_id"] == seeded_vehicle.id
        ]
        assert len(matching) >= 1, "En az bir HIGH_RISK alert bekleniyor"

    async def test_safe_temp_creates_no_alert(
        self, client, seeded_vehicle
    ) -> None:
        payload = {"gps_lat": 40.0, "gps_lng": 28.0, "current_temp_c": 4.0}
        await client.post(
            f"/api/fleet/{seeded_vehicle.id}/telemetry", json=payload
        )

        alerts_resp = await client.get("/api/alerts/")
        matching = [
            a for a in alerts_resp.json()
            if a["entity_id"] == seeded_vehicle.id
        ]
        assert matching == [], "Güvenli sıcaklıkta alert beklenmemeli"
