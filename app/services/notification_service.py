import uuid
from datetime import datetime, timezone

from app.repositories.base_repository import BaseRepository


class NotificationService(BaseRepository):
    collection_name = 'notifications'

    def create_notification(self, user_id, title, message):
        notification = {
            'id': str(uuid.uuid4()),
            'user_id': user_id,
            'title': title,
            'message': message,
            'is_read': False,
            'created_at': datetime.now(timezone.utc).isoformat(),
        }
        return self.create(notification)

    def get_for_user(self, user_id):
        return sorted(
            [notification for notification in self.get_all() if notification.get('user_id') == user_id],
            key=lambda notification: notification.get('created_at', ''),
            reverse=True,
        )

    def mark_read(self, notification_id, user_id):
        notification = self.get_by_id(notification_id)
        if not notification or notification.get('user_id') != user_id:
            return False
        return self.update(notification_id, {'is_read': True})
