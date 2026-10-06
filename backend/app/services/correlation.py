import re

from app.core.database import DetectionRecord, ReportRecord, SubmissionRecord
from app.services.previous_report_matcher import MATCH_THRESHOLD, _normalize_content, _similarity_score
from app.services.url_analysis import analyze_url


ENTITY_MODELS = {
    "submission": SubmissionRecord,
    "report": ReportRecord,
    "detection": DetectionRecord,
}
RELATIONSHIP_TYPES = {
    "similar_content", "same_reported_content", "same_sender", "same_url_domain", "related_report"
}


def _submission_for(db, entity_type: str, entity_id: str):
    entity = db.get(ENTITY_MODELS[entity_type], entity_id)
    if entity is None:
        return None
    if entity_type == "submission":
        return entity
    return db.get(SubmissionRecord, entity.submission_id)


def validate_relationship(db, relationship_type, source_type, source_id, target_type, target_id):
    if relationship_type not in RELATIONSHIP_TYPES:
        raise ValueError("Unsupported relationship type")
    if source_type not in ENTITY_MODELS or target_type not in ENTITY_MODELS:
        raise ValueError("Unsupported entity type")
    if source_type == target_type and source_id == target_id:
        raise ValueError("A relationship requires two distinct entities")

    if relationship_type == "related_report":
        if source_type != "report" or target_type != "report":
            raise ValueError("related_report requires two reports")
        source_report = db.get(ReportRecord, source_id)
        target_report = db.get(ReportRecord, target_id)
        if not source_report or not target_report or source_report.submission_id != target_report.submission_id:
            raise ValueError("Reports are not deterministically related")
        return {"shared_submission_id": source_report.submission_id}

    source = _submission_for(db, source_type, source_id)
    target = _submission_for(db, target_type, target_id)
    if source is None or target is None:
        raise LookupError("Entity not found")

    if relationship_type == "same_sender":
        left, right = source.sender, target.sender
        valid = bool(left and right and left.strip().casefold() == right.strip().casefold())
        evidence = {"sender": left.strip() if valid else None}
    elif relationship_type == "same_url_domain":
        try:
            left_domain = analyze_url(source.url).registrable_domain if source.url else None
            right_domain = analyze_url(target.url).registrable_domain if target.url else None
        except ValueError:
            left_domain = right_domain = None
        valid = bool(left_domain and left_domain == right_domain)
        evidence = {"registrable_domain": left_domain if valid else None}
    else:
        left = _normalize_content(source.text, source.caption, source.url)
        right = _normalize_content(target.text, target.caption, target.url)
        if relationship_type == "same_reported_content":
            valid = bool(left and left == right)
            evidence = {"match": "exact_normalized_content"}
        else:
            score = _similarity_score(left, right) if left and right else None
            valid = score is not None and score >= MATCH_THRESHOLD
            evidence = {"similarity_score": score}
    if not valid:
        raise ValueError("The requested relationship is not supported by matching stored data")
    return evidence
