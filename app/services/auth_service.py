from flask_bcrypt import check_password_hash, generate_password_hash

from app.repositories.user_repository import UserRepository


class AuthService:
    def __init__(self):
        self.user_repository = UserRepository()

    def register(self, payload):
        email_value = payload.get('email')
        email = email_value.strip().lower() if isinstance(email_value, str) else ''
        if not email:
            raise ValueError('Email is required.')
        password = payload.get('password')
        if not isinstance(password, str) or len(password) < 8:
            raise ValueError('Password must be at least 8 characters long.')
        role = payload.get('role', 'candidate')
        if not isinstance(role, str) or role not in {'candidate', 'recruiter'}:
            raise ValueError('Only candidate and recruiter accounts can be registered.')
        skills = payload.get('skills', [])
        if not isinstance(skills, list) or any(not isinstance(skill, str) for skill in skills):
            raise ValueError('Skills must be a list of text values.')
        if self.user_repository.get_by_email(email):
            raise ValueError('User already exists.')
        user = {
            'email': email,
            'password_hash': generate_password_hash(password).decode('utf-8'),
            'role': role,
            'full_name': payload.get('full_name', ''),
            'phone': payload.get('phone', ''),
            'location': payload.get('location', ''),
            'skills': skills,
        }
        return self.user_repository.create_user(user)

    def login(self, email, password):
        if not isinstance(email, str) or not isinstance(password, str):
            return None
        user = self.user_repository.get_by_email(email.strip().lower())
        if not user or not check_password_hash(user.get('password_hash', ''), password):
            return None
        return user

    def seed_admin(self, email='admin@hirehub.local', password='admin123'):
        if not self.user_repository.get_by_email(email):
            self.user_repository.create_user({
                'email': email,
                'password_hash': generate_password_hash(password).decode('utf-8'),
                'role': 'admin',
                'full_name': 'System Admin',
                'phone': '0000000000',
                'location': 'HQ',
            })
