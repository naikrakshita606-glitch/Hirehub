import uuid

from app.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository):
    collection_name = 'users'

    def create_user(self, user_data):
        user_data = dict(user_data)
        user_data.setdefault('id', str(uuid.uuid4()))
        return self.create(user_data)

    def get_by_email(self, email):
        for user in self.get_all():
            if user.get('email', '').lower() == email.lower():
                return user
        return None

    def update_profile(self, user_id, updates):
        allowed_fields = {'full_name', 'phone', 'location', 'skills', 'experience', 'summary', 'resume_filename'}
        return self.update(user_id, {key: value for key, value in updates.items() if key in allowed_fields})
