from dataclasses import dataclass

from app.models.user import User


@dataclass
class Admin(User):
    permission_level: str = 'full'

    @staticmethod
    def from_dict(data):
        return Admin(
            id=str(data.get('id') or data.get('_id') or ''),
            email=data.get('email', ''),
            password_hash=data.get('password_hash', ''),
            role='admin',
            full_name=data.get('full_name', ''),
            phone=data.get('phone', ''),
            location=data.get('location', ''),
            skills=data.get('skills', []),
            permission_level=data.get('permission_level', 'full'),
        )
