from dataclasses import dataclass, field

from app.models.user import User


@dataclass
class Recruiter(User):
    company_name: str = ''
    department: str = ''
    hiring_targets: list[str] = field(default_factory=list)

    @staticmethod
    def from_dict(data):
        return Recruiter(
            id=str(data.get('id') or data.get('_id') or ''),
            email=data.get('email', ''),
            password_hash=data.get('password_hash', ''),
            role='recruiter',
            full_name=data.get('full_name', ''),
            phone=data.get('phone', ''),
            location=data.get('location', ''),
            skills=data.get('skills', []),
            company_name=data.get('company_name', ''),
            department=data.get('department', ''),
            hiring_targets=data.get('hiring_targets', []),
        )
