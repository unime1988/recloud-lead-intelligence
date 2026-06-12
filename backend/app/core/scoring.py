"""Lead scoring engine — optimised for Rachel AI interview-SaaS sales.

Each rule contributes points; the total maps to a priority band. The
open-jobs thresholds are tiered (the highest matching tier is used, not
summed), while every other signal is an independent additive contribution.
"""

from dataclasses import dataclass, field


@dataclass
class SignalInput:
    total_open_jobs: int = 0
    recruiter_jobs_open: int = 0
    ta_coordinator_jobs: int = 0
    high_volume_role_jobs: int = 0
    has_urgent_hiring: bool = False
    has_multiple_locations: bool = False
    has_stale_jobs: bool = False
    decision_maker_found: bool = False
    is_agency: bool = False


@dataclass
class ScoreBreakdownItem:
    label: str
    points: int


@dataclass
class ScoreResult:
    score: int
    priority: str
    breakdown: list[ScoreBreakdownItem] = field(default_factory=list)

    def as_signals(self) -> list[dict]:
        return [{"label": item.label, "points": item.points} for item in self.breakdown]


def _open_jobs_points(total_open_jobs: int) -> ScoreBreakdownItem | None:
    """Tiered: use the single highest matching threshold."""
    if total_open_jobs >= 500:
        return ScoreBreakdownItem("500+ open jobs — massive interview volume", 10)
    if total_open_jobs >= 200:
        return ScoreBreakdownItem("200+ open jobs — enterprise scale", 8)
    if total_open_jobs >= 100:
        return ScoreBreakdownItem("100+ open jobs", 6)
    if total_open_jobs >= 50:
        return ScoreBreakdownItem("50+ open jobs", 4)
    if total_open_jobs >= 20:
        return ScoreBreakdownItem("20+ open jobs", 2)
    return None


def priority_for_score(score: int) -> str:
    if score >= 18:
        return "Very Hot"
    if score >= 12:
        return "High"
    if score >= 6:
        return "Medium"
    return "Low"


def score_lead(signal: SignalInput) -> ScoreResult:
    breakdown: list[ScoreBreakdownItem] = []

    open_jobs_item = _open_jobs_points(signal.total_open_jobs)
    if open_jobs_item:
        breakdown.append(open_jobs_item)

    if signal.recruiter_jobs_open >= 1:
        breakdown.append(ScoreBreakdownItem("Hiring recruiter/TA", 2))
    if signal.recruiter_jobs_open >= 2:
        breakdown.append(ScoreBreakdownItem("Hiring multiple recruiters", 4))

    if signal.ta_coordinator_jobs >= 1:
        breakdown.append(ScoreBreakdownItem("TA coordinator / recruitment ops role", 3))

    if signal.has_urgent_hiring:
        breakdown.append(ScoreBreakdownItem("Urgent hiring keywords", 2))

    if signal.has_multiple_locations:
        breakdown.append(ScoreBreakdownItem("Hiring across multiple locations", 3))

    if signal.high_volume_role_jobs >= 1:
        breakdown.append(ScoreBreakdownItem("High-volume roles (sales/support/BPO/ops)", 4))

    if signal.has_stale_jobs:
        breakdown.append(ScoreBreakdownItem("Stale postings — possible interview bottleneck", 3))

    if signal.decision_maker_found:
        breakdown.append(ScoreBreakdownItem("Decision-maker found", 3))

    if signal.is_agency:
        breakdown.append(ScoreBreakdownItem("Recruitment/consulting agency — high interview volume", 5))

    score = sum(item.points for item in breakdown)
    return ScoreResult(score=score, priority=priority_for_score(score), breakdown=breakdown)
