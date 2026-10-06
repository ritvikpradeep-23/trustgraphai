import re
from dataclasses import dataclass
from datetime import datetime, timezone
from difflib import SequenceMatcher
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import ReportMatchRecord, ReportRecord, SubmissionRecord


# Reproduced against the 300-pattern catalog by scripts/calibrate_demo_threshold.py on 13 unseeded scam
# paraphrases and 16 benign controls (including similar scam warnings).
# This is demo calibration, not independent real-world validation.
MATCH_THRESHOLD = 0.712
MIN_CONTENT_LENGTH = 24


def similarity_tier(score: float) -> str:
    if score == 1:
        return "Exact"
    if score >= .90:
        return "Very strong"
    if score >= .80:
        return "Strong"
    if score >= MATCH_THRESHOLD:
        return "Partial"
    return "Below threshold"


@dataclass
class PreviousReportMatch:
    report_id: str
    submission_id: str
    report_type: str
    status: str
    similarity_score: float


def _normalize_content(*parts: str | None) -> str:
    content = " ".join(part for part in parts if part)
    return " ".join(re.findall(r"\w+", content.casefold()))


def _similarity_score(candidate: str, reported: str) -> float | None:
    if min(len(candidate), len(reported)) < MIN_CONTENT_LENGTH:
        return None

    candidate_tokens = set(candidate.split())
    reported_tokens = set(reported.split())
    if not candidate_tokens or not reported_tokens:
        return None

    token_similarity = len(candidate_tokens & reported_tokens) / len(candidate_tokens | reported_tokens)
    sequence_similarity = SequenceMatcher(None, candidate, reported).ratio()
    return round((token_similarity + sequence_similarity) / 2, 3)


def find_previous_report_matches(
    db: Session,
    *,
    text: str,
    url: str | None,
    submission_id: str | None,
    include_below_threshold: bool = False,
) -> list[PreviousReportMatch]:
    candidate = _normalize_content(text, url)
    if len(candidate) < MIN_CONTENT_LENGTH:
        return []

    statement = select(ReportRecord, SubmissionRecord).join(
        SubmissionRecord, ReportRecord.submission_id == SubmissionRecord.submission_id
    )
    matches: list[PreviousReportMatch] = []

    for report, reported_submission in db.execute(statement):
        if reported_submission.submission_id == submission_id:
            continue

        reported_content = _normalize_content(
            reported_submission.text,
            reported_submission.caption,
            reported_submission.url,
        )
        similarity_score = _similarity_score(candidate, reported_content)
        if similarity_score is not None and (include_below_threshold or similarity_score >= MATCH_THRESHOLD):
            matches.append(
                PreviousReportMatch(
                    report_id=report.report_id,
                    submission_id=reported_submission.submission_id,
                    report_type=report.report_type,
                    status=report.status,
                    similarity_score=similarity_score,
                )
            )

    return sorted(matches, key=lambda match: (-match.similarity_score, match.report_id))


def store_previous_report_matches(
    db: Session,
    *,
    submission_id: str,
    matches: list[PreviousReportMatch],
) -> None:
    for match in matches:
        existing_match = db.scalar(
            select(ReportMatchRecord.match_id).where(
                ReportMatchRecord.submission_id == submission_id,
                ReportMatchRecord.report_id == match.report_id,
            )
        )
        if existing_match is None:
            db.add(
                ReportMatchRecord(
                    match_id=f"match_{uuid4().hex[:12]}",
                    submission_id=submission_id,
                    report_id=match.report_id,
                    matched_submission_id=match.submission_id,
                    similarity_score=match.similarity_score,
                    created_at=datetime.now(timezone.utc),
                )
            )

    db.commit()
