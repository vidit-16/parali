"""Money for one field and season: advance before harvest, balance or recovery after the satellite check.

Advance rule: a field gets the advance only if last season's check came out clean. One clean season is
enough to earn it back after a burn.

Rates are per state, because the incentive is a state scheme. The advance is half, so it covers hiring a
baler or a happy seeder in the weeks between harvest and sowing, which is when the money is short.
"""
from dataclasses import dataclass

SEASON = ("2025-10-01", "2025-11-30")       # claim window: harvest to sowing
PREV_SEASON = ("2024-10-01", "2024-11-30")  # decides the advance


@dataclass(frozen=True)
class Scheme:
    state: str
    rate_per_acre: int
    advance_share: float
    basis: str


SCHEMES = {
    "HR": Scheme("Haryana", 1000, 0.5, "Haryana Rajya Vishisht Yojana (2024): Rs 1,000 per acre for not burning"),
    "PB": Scheme("Punjab", 1000, 0.5, "No Punjab per-acre scheme is paying out; the pilot uses Haryana's rate"),
}
# Smoke estimate: about 2.6 t of paddy straw per acre in Punjab, about 80% of it burnt when a field is set on fire,
# about 9 kg of PM2.5 per tonne burnt (published emission factors for rice straw run about 8-12 kg). An estimate
# for scale, not a measurement. CO2 is left out: it is mostly carbon the crop took in that season.
# 2.6 t of straw an acre, 80% of it burnt, about 9 kg of PM2.5 a tonne burnt (published range 8-12 kg).
# The web app uses the same 18.72 (shared.js, explorer.js); tests/test_parity.py keeps them equal.
PM25_KG_PER_ACRE = 2.6 * 0.8 * 9


def smoke_kg(acres: float | None) -> int:
    return int(round((acres or 0) * PM25_KG_PER_ACRE))


DEFAULT_STATE = "PB"  # the labelled study area is Patran tehsil, Patiala

CLEAN = ("auto_approved", "officer_approved")
PENDING = ("submitted", "needs_review", "possible_burn")

# CAQM (Environmental Compensation for Stubble Burning) Amendment Rules, 2024: per incident, by landholding.
COMPENSATION_TIERS = ((2.0, 5000), (5.0, 10000), (float("inf"), 30000))


def scheme(state: str | None) -> Scheme:
    return SCHEMES.get(state or DEFAULT_STATE, SCHEMES[DEFAULT_STATE])


def full_amount(acres: float, state: str | None = None) -> int:
    return round(acres * scheme(state).rate_per_acre)


def advance_amount(acres: float, state: str | None = None) -> int:
    s = scheme(state)
    return round(acres * s.rate_per_acre * s.advance_share)


def advance_eligible(prev_outcome: str | None) -> bool:
    return prev_outcome in CLEAN


def environmental_compensation(acres: float) -> int:
    return next(amount for limit, amount in COMPENSATION_TIERS if acres < limit)


def settle(status: str, acres: float, advance_paid: int, state: str | None = None) -> dict:
    """What happens to the money once the season's check is decided."""
    total = full_amount(acres, state)
    if status in CLEAN:
        return {"state": "balance_due", "balance": total - advance_paid, "recover": 0, "total": total}
    if status == "officer_confirmed_burnt":
        return {"state": "recover_advance" if advance_paid else "not_payable", "balance": 0,
                "recover": advance_paid, "total": total,
                "compensation_reference": environmental_compensation(acres)}
    return {"state": "pending", "balance": None, "recover": None, "total": total}
