"""Money for one field and season: advance before harvest, balance or recovery after the satellite check.

Advance rule: a field gets the advance only if last season's check came out clean. One clean season is
enough to earn it back after a burn.
"""
SEASON = ("2025-10-01", "2025-11-30")       # claim window: harvest to sowing
PREV_SEASON = ("2024-10-01", "2024-11-30")  # decides the advance
RATE_PER_ACRE = 1200       # Haryana crop residue management incentive, 2025
ADVANCE_SHARE = 0.25       # share paid before harvest

CLEAN = ("auto_approved", "officer_approved")
PENDING = ("submitted", "needs_review", "possible_burn")

# CAQM (Environmental Compensation for Stubble Burning) Amendment Rules, 2024: per incident, by landholding.
COMPENSATION_TIERS = ((2.0, 5000), (5.0, 10000), (float("inf"), 30000))


def full_amount(acres: float) -> int:
    return round(acres * RATE_PER_ACRE)


def advance_amount(acres: float) -> int:
    return round(acres * RATE_PER_ACRE * ADVANCE_SHARE)


def advance_eligible(prev_outcome: str | None) -> bool:
    return prev_outcome in CLEAN


def environmental_compensation(acres: float) -> int:
    return next(amount for limit, amount in COMPENSATION_TIERS if acres < limit)


def settle(status: str, acres: float, advance_paid: int) -> dict:
    """What happens to the money once the season's check is decided."""
    total = full_amount(acres)
    if status in CLEAN:
        return {"state": "balance_due", "balance": total - advance_paid, "recover": 0, "total": total}
    if status == "officer_confirmed_burnt":
        return {"state": "recover_advance" if advance_paid else "not_payable", "balance": 0,
                "recover": advance_paid, "total": total,
                "compensation_reference": environmental_compensation(acres)}
    return {"state": "pending", "balance": None, "recover": None, "total": total}
