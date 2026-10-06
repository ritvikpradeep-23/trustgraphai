from app.schemas.submission import Submission


def process_submission(submission: Submission) -> dict:
    """
    Normalize a Universal Submission into a common
    representation for the TrustGraph analysis pipeline.
    """

    return {
        "submission_id": submission.submission_id,
        "source": submission.source.value,
        "content_type": submission.content_type.value,
        "text": submission.text,
        "caption": submission.caption,
        "url": submission.url,
        "media_reference": submission.media_reference,
        "sender": submission.sender,
        "source_timestamp": submission.source_timestamp,
        "user_consent": submission.user_consent,
        "created_at": submission.created_at,
    }