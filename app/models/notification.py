from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class Notification:
    id: str = ''
    user_id: str = ''
    title: str = ''
    message: str = ''
    is_read: bool = False
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
