import math
from typing import Optional

# ── Spoilage index ────────────────────────────────────────────────────────────
# Bk = t * exp(0.1 * T)
#   t : collection elapsed time in hours
#   T : milk temperature in °C
# Formula lives ONLY here — never compute Bk outside this module.

BK_HIGH_RISK: float = 8.0    # Bk > 8.0 → HIGH_RISK
BK_MEDIUM_RISK: float = 4.0  # Bk > 4.0 → MEDIUM_RISK

# Cold-chain safe window for vehicle milk tanks
COLD_CHAIN_MIN: float = 2.0  # °C — below this is also a breach
COLD_CHAIN_MAX: float = 6.0  # °C — above this triggers alert immediately


def calculate_spoilage(t: float, T: float) -> float:
    """Return spoilage index Bk for elapsed time t (hours) at temperature T (°C)."""
    return t * math.exp(0.1 * T)


def check_spoilage_alert(
    t: float, T: float, entity_id: int, entity_type: str
) -> Optional[dict]:
    """
    Evaluate only the Bk threshold rules.
    Cold-chain T violations are handled separately by check_cold_chain_alert
    to avoid generating duplicate HIGH_RISK alerts for the same event.
    """
    bk = calculate_spoilage(t, T)
    if bk > BK_HIGH_RISK:
        return {
            "alert_type": "HIGH_RISK",
            "severity": "critical",
            "message": (
                f"Yüksek bozulma riski — Bk={bk:.2f} "
                f"(T={T:.1f}°C, t={t:.1f}h) | {entity_type} #{entity_id}"
            ),
            "entity_id": entity_id,
            "entity_type": entity_type,
        }
    if bk > BK_MEDIUM_RISK:
        return {
            "alert_type": "MEDIUM_RISK",
            "severity": "high",
            "message": (
                f"Orta bozulma riski — Bk={bk:.2f} "
                f"(T={T:.1f}°C, t={t:.1f}h) | {entity_type} #{entity_id}"
            ),
            "entity_id": entity_id,
            "entity_type": entity_type,
        }
    return None


def check_cold_chain_alert(
    entity_id: int, entity_type: str, temperature: float
) -> Optional[dict]:
    """
    Fires IMMEDIATELY when temperature leaves the [+2 °C, +6 °C] window.
    Per CLAUDE.md: her iki yönde de ihlal HIGH_RISK üretir.
    """
    if temperature > COLD_CHAIN_MAX:
        return {
            "alert_type": "HIGH_RISK",
            "severity": "critical",
            "message": (
                f"Soğuk zincir ihlali — sıcaklık çok yüksek: "
                f"{temperature:.1f}°C (limit: {COLD_CHAIN_MAX}°C) | "
                f"{entity_type} #{entity_id}"
            ),
            "entity_id": entity_id,
            "entity_type": entity_type,
        }
    if temperature < COLD_CHAIN_MIN:
        return {
            "alert_type": "HIGH_RISK",
            "severity": "high",
            "message": (
                f"Soğuk zincir ihlali — sıcaklık çok düşük: "
                f"{temperature:.1f}°C (limit: {COLD_CHAIN_MIN}°C) | "
                f"{entity_type} #{entity_id}"
            ),
            "entity_id": entity_id,
            "entity_type": entity_type,
        }
    return None


def check_tank_level_alert(
    tank_id: int, current_level: float, capacity: float
) -> Optional[dict]:
    fill_pct = (current_level / capacity * 100) if capacity > 0 else 0.0
    if fill_pct >= 90:
        return {
            "alert_type": "tank_overflow",
            "severity": "high",
            "message": (
                f"Tank #{tank_id} doluluk oranı %{fill_pct:.1f} — "
                f"taşma riski var"
            ),
            "entity_id": tank_id,
            "entity_type": "tank",
        }
    if fill_pct < 10:
        return {
            "alert_type": "low_tank",
            "severity": "medium",
            "message": f"Tank #{tank_id} doluluk oranı düşük: %{fill_pct:.1f}",
            "entity_id": tank_id,
            "entity_type": "tank",
        }
    return None
