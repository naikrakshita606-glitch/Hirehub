from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class Job:
    id: str = ''
    title: str = ''
    company: str = ''
    location: str = ''
    salary: str = ''
    job_type: str = 'full-time'
    description: str = ''
    requirements: list[str] = field(default_factory=list)
    recruiter_id: str = ''
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @staticmethod
    def from_dict(data):
        return Job(
            id=str(data.get('id') or data.get('_id') or ''),
            title=data.get('title', ''),
            company=data.get('company', ''),
            location=data.get('location', ''),
            salary=data.get('salary', ''),
            job_type=data.get('job_type', 'full-time'),
            description=data.get('description', ''),
            requirements=data.get('requirements', []),
            recruiter_id=data.get('recruiter_id', ''),
            created_at=data.get('created_at', datetime.now(timezone.utc).isoformat()),
        )
