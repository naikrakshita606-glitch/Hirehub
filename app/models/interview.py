from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class Interview:
    id: str = ''
    application_id: str = ''
    candidate_id: str = ''
    recruiter_id: str = ''
    scheduled_at: str = ''
    mode: str = 'virtual'
    status: str = 'scheduled'
    notes: str = ''
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
