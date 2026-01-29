
from sqlalchemy.orm import Session
from app.db.models import SpecDocument, SpecStatus

def assert_spec_approved(db: Session, story_id: str) -> None:
    doc = (
        db.query(SpecDocument)
        .filter(SpecDocument.story_id == story_id, SpecDocument.status == SpecStatus.approved)
        .order_by(SpecDocument.version.desc())
        .first()
    )
    if not doc:
        raise ValueError("Spec not approved for this story. Please approve a spec before code generation.")
