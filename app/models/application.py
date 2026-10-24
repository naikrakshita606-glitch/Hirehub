from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class Application:
    id: str = ''
    job_id: str = ''
    candidate_id: str = ''
    recruiter_id: str = ''
    status: str = 'applied'
    cover_letter: str = ''
    applied_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @staticmethod
    def from_dict(data):
        return Application(
            id=str(data.get('id') or data.get('_id') or ''),
            job_id=data.get('job_id', ''),
            candidate_id=data.get('candidate_id', ''),
            recruiter_id=data.get('recruiter_id', ''),
            status=data.get('status', 'applied'),
            cover_letter=data.get('cover_letter', ''),
            applied_at=data.get('applied_at', datetime.now(timezone.utc).isoformat()),
        )
