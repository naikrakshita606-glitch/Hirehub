from datetime import datetime, timezone

from app.repositories.base_repository import BaseRepository


class AuditService(BaseRepository):
    collection_name = 'audit_logs'

    def record(self, actor_id, action, entity_type, entity_id, details=''):
        return self.create({
            'actor_id': str(actor_id),
            'action': action,
            'entity_type': entity_type,
            'entity_id': str(entity_id),
            'details': details,
            'created_at': datetime.now(timezone.utc).isoformat(),
        })

    def get_recent(self, limit=200):
        return sorted(self.get_all(), key=lambda item: item.get('created_at', ''), reverse=True)[:limit]
