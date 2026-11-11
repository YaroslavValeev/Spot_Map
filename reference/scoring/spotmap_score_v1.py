"""SpotMap SpotScore v1.0.0 — reference deterministic scorer, standard library only.
Not a validated production rating engine. Review abuse identification and safety
verification happen upstream; caller must provide flags and moderated observations.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from decimal import Decimal, ROUND_HALF_UP
from math import exp
from typing import Iterable

PROFILES = {
    "wakesurf_v1": {
        "riding_conditions": 0.20, "coaching": 0.15,
        "equipment": 0.15, "safety": 0.20, "service": 0.10,
        "infrastructure": 0.10, "value": 0.10,
    },
    "wakeboard_cable_v1": {
        "course_setup": 0.20, "coaching": 0.10,
        "equipment": 0.20, "safety": 0.20, "service": 0.10,
        "infrastructure": 0.10, "value": 0.10,
    },
}
assert all(abs(sum(w.values()) - 1.0) < 1e-9 for w in PROFILES.values())

@dataclass(frozen=True)
class Observation:
    domain: str
    value: float                 # 0..100; review stars converted upstream
    kind: str                   # independent_expert | verified_visit | unverified_visit
    age_days: float = 0.0
    fraud_factor: float = 1.0   # moderated [0,1]
    conflict_of_interest: bool = False
    author_id: str | None = None
    period_key: str | None = None  # YYYY-Q or 90-day moderation bucket

@dataclass(frozen=True)
class Result:
    score: int | None
    raw_score: float | None
    status: str
    coverage: float
    n_total: float
    per_domain: dict
    formula_version: str = "1.0.0"
    profile: str = "wakesurf_v1"

BASE = {"independent_expert": 3.0, "verified_visit": 1.0, "unverified_visit": 0.35}


def compute(
    profile: str,
    observations: Iterable[Observation],
    *,
    safety_check_verified: bool,
    critical_safety_issue: bool = False,
    verified_visits: int = 0,
    independent_source_groups: int = 1,
    independent_deep_audit: bool = False,
    unresolved_identity_conflict: bool = False,
    prior: float = 65.0,
    kappa: float = 3.0,
) -> Result:
    if profile not in PROFILES:
        raise ValueError(f"Unknown profile: {profile}")
    if not (0 <= prior <= 100 and kappa > 0):
        raise ValueError("Invalid prior")
    domains = PROFILES[profile]
    grouped = {d: [] for d in domains}
    seen = set()
    for o in observations:
        if o.domain not in grouped:
            raise ValueError(f"Unknown domain: {o.domain}")
        if o.kind not in BASE or not (0 <= o.value <= 100):
            raise ValueError("Invalid observation")
        if o.age_days < 0 or not (0 <= o.fraud_factor <= 1):
            raise ValueError("Invalid observation weight")
        if o.conflict_of_interest or o.fraud_factor == 0:
            continue
        # Caller supplies 90-day moderation bucket; refuse duplicate same-author
        # assessments for same subject/domain/bucket. Subject is external to this scorer.
        if o.author_id is not None and o.period_key is not None:
            key = (o.domain, o.kind, o.author_id, o.period_key)
            if key in seen:
                continue
            seen.add(key)
        w = BASE[o.kind] * exp(-o.age_days / 365.0) * o.fraud_factor
        if w > 0:
            grouped[o.domain].append((o.value, w))
    per = {}
    coverage = 0.0
    total_eff = 0.0
    total_weight = 0.0
    weighted = 0.0
    for domain, W in domains.items():
        vals = grouped[domain]
        n = sum(w for _, w in vals)
        total_eff += n
        if n >= 1.0:
            coverage += W
        if n > 0:
            D = (kappa * prior + sum(x*w for x,w in vals))/(kappa+n)
            total_weight += W
            weighted += W*D
            per[domain] = {"weight": W, "posterior": round(D, 4), "n_eff": round(n, 4)}
        else:
            per[domain] = {"weight": W, "posterior": None, "n_eff": 0.0}
    coverage = round(coverage, 6)
    total_eff = round(total_eff, 6)
    raw = weighted / total_weight if total_weight else None
    status = "unrated"
    if critical_safety_issue:
        status = "restricted"
    elif not unresolved_identity_conflict and safety_check_verified and coverage >= 0.65 and total_eff >= 4.0:
        status = "preliminary"
        if (coverage >= 0.85 and total_eff >= 12.0 and independent_source_groups >= 2
                and (verified_visits >= 3 or independent_deep_audit)):
            status = "verified"
    score = (int(Decimal(str(raw)).quantize(Decimal('1'), rounding=ROUND_HALF_UP))
             if raw is not None and status in ('preliminary', 'verified') else None)
    return Result(score=score, raw_score=round(raw, 6) if score is not None else None,
                  status=status, coverage=coverage, n_total=total_eff,
                  per_domain=per, profile=profile)

if __name__ == "__main__":
    example = [Observation(d, x, 'independent_expert') for d, x in zip(
        PROFILES['wakesurf_v1'], [90, 85, 88, 92, 80, 70, 75])]
    print(asdict(compute('wakesurf_v1', example, safety_check_verified=True)))
