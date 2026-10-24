import uuid
from datetime import datetime, timezone

from app.repositories.interview_repository import InterviewRepository
from app.repositories.application_repository import ApplicationRepository
from app.services.audit_service import AuditService
from app.services.notification_service import NotificationService


class InterviewService:
    def __init__(self):
        self.interview_repository = InterviewRepository()
        self.application_repository = ApplicationRepository()
        self.notifications = NotificationService()
        self.audit = AuditService()

    def schedule(self, payload):
        application = self.application_repository.get_by_id(payload.get('application_id'))
        recruiter_id = str(payload.get('recruiter_id', ''))
        if not application or application.get('recruiter_id') != recruiter_id:
            raise ValueError('Application not found.')
        scheduled_value = payload.get('scheduled_at', '')
        if not isinstance(scheduled_value, str):
            raise ValueError('Provide a valid interview date and time.')
        scheduled_at = scheduled_value.strip()
        try:
            parsed_at = datetime.fromisoformat(scheduled_at.replace('Z', '+00:00'))
        except (TypeError, ValueError) as exc:
            raise ValueError('Provide a valid interview date and time.') from exc
        if parsed_at.tzinfo is None:
            parsed_at = parsed_at.replace(tzinfo=timezone.utc)
        if parsed_at <= datetime.now(timezone.utc):
            raise ValueError('Interview must be scheduled in the future.')
        mode = payload.get('mode', 'virtual')
        if not isinstance(mode, str) or mode not in {'virtual', 'in-person', 'phone'}:
            raise ValueError('Select a valid interview mode.')
        interview = {
            'id': str(uuid.uuid4()),
            'application_id': str(application['id']),
            'candidate_id': str(application['candidate_id']),
            'recruiter_id': recruiter_id,
            'scheduled_at': parsed_at.astimezone(timezone.utc).isoformat(),
            'mode': mode,
            'status': 'scheduled',
            'notes': payload.get('notes', ''),
        }
        created = self.interview_repository.create(interview)
        self.notifications.create_notification(
            interview['candidate_id'], 'Interview scheduled',
            f"An interview has been scheduled for {interview['scheduled_at']}.",
        )
        self.audit.record(recruiter_id, 'interview.scheduled', 'interview', created['id'])
        return created

    def update(self, interview_id, recruiter_id, payload):
        interview = self.interview_repository.get_by_id(interview_id)
        recruiter_id = str(recruiter_id)
        if not interview or interview.get('recruiter_id') != recruiter_id:
            raise ValueError('Interview not found.')
        updates = {}
        if 'scheduled_at' in payload:
            value = payload['scheduled_at']
            if not isinstance(value, str):
                raise ValueError('Provide a valid interview date and time.')
            try:
                parsed_at = datetime.fromisoformat(value.replace('Z', '+00:00'))
            except ValueError as exc:
                raise ValueError('Provide a valid interview date and time.') from exc
            if parsed_at.tzinfo is None:
                parsed_at = parsed_at.replace(tzinfo=timezone.utc)
            if parsed_at <= datetime.now(timezone.utc):
                raise ValueError('Interview must be scheduled in the future.')
            updates['scheduled_at'] = parsed_at.astimezone(timezone.utc).isoformat()
        if 'mode' in payload:
            mode = payload['mode']
            if not isinstance(mode, str) or mode not in {'virtual', 'in-person', 'phone'}:
                raise ValueError('Select a valid interview mode.')
            updates['mode'] = mode
        if 'notes' in payload:
            if not isinstance(payload['notes'], str):
                raise ValueError('Interview notes must be text.')
            updates['notes'] = payload['notes'].strip()
        if 'status' in payload:
            status = payload['status']
            if not isinstance(status, str) or status not in {'cancelled', 'completed'}:
                raise ValueError('Interview status must be cancelled or completed.')
            if interview.get('status') != 'scheduled':
                raise ValueError('Only scheduled interviews can be cancelled or completed.')
            updates['status'] = status
        if not updates:
            raise ValueError('Provide at least one interview field to update.')
        self.interview_repository.update(interview_id, updates)
        self.notifications.create_notification(
            interview['candidate_id'],
            'Interview updated',
            f"Your interview has been {updates.get('status', 'updated')}: "
            f"{updates.get('scheduled_at', interview.get('scheduled_at', ''))}.",
        )
        self.audit.record(recruiter_id, 'interview.updated', 'interview', interview_id)
        interview.update(updates)
        return interview
