from dataclasses import dataclass, field

from app.models.user import User


@dataclass
class Candidate(User):
    experience: str = '0 years'
    summary: str = ''
    resume_url: str = ''
    preferred_roles: list[str] = field(default_factory=list)

    @staticmethod
    def from_dict(data):
        return Candidate(
            id=str(data.get('id') or data.get('_id') or ''),
            email=data.get('email', ''),
            password_hash=data.get('password_hash', ''),
            role='candidate',
            full_name=data.get('full_name', ''),
            phone=data.get('phone', ''),
            location=data.get('location', ''),
            skills=data.get('skills', []),
            experience=data.get('experience', '0 years'),
            summary=data.get('summary', ''),
            resume_url=data.get('resume_url', ''),
            preferred_roles=data.get('preferred_roles', []),
        )
