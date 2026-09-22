from sqlalchemy.orm import Session

from app.models.models import AuditLog


def log(db: Session, application_id, action: str, actor: str, details: dict | None = None, commit: bool = True):
    entry = AuditLog(application_id=application_id, action=action, actor=actor, details=details or {})
    db.add(entry)
    if commit:
        db.commit()
    return entry
