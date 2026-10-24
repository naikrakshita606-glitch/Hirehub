import uuid
from datetime import datetime, timezone

from pymongo.errors import DuplicateKeyError

from app.repositories.application_repository import ApplicationRepository
from app.repositories.job_repository import JobRepository
from app.services.audit_service import AuditService
from app.services.notification_service import NotificationService


class ApplicationService:
    def __init__(self):
        self.application_repository = ApplicationRepository()
        self.job_repository = JobRepository()
        self.notifications = NotificationService()
        self.audit = AuditService()

    def apply(self, payload):
        job = self.job_repository.get_by_id(payload.get('job_id'))
        if not job or job.get('status', 'published') != 'published':
            raise ValueError('This job is not available.')
        if self.application_repository.get_by_candidate_and_job(payload.get('candidate_id'), payload.get('job_id')):
            raise ValueError('You have already applied to this job.')
        application = {
            'id': str(uuid.uuid4()),
            'job_id': str(job['id']),
            'candidate_id': str(payload['candidate_id']),
            'recruiter_id': str(job.get('recruiter_id', '')),
            'status': 'applied',
            'cover_letter': payload.get('cover_letter', ''),
            'created_at': datetime.now(timezone.utc).isoformat(),
        }
        try:
            created = self.application_repository.create(application)
        except DuplicateKeyError as exc:
            raise ValueError('You have already applied to this job.') from exc
        self.notifications.create_notification(
            application['recruiter_id'], 'New application',
            f"A candidate applied for {job.get('title', 'your job')}.",
        )
        self.audit.record(application['candidate_id'], 'application.created', 'application', created['id'])
        return created

    def update_status(self, application_id, recruiter_id, status):
        if status not in {'reviewing', 'shortlisted', 'rejected', 'hired'}:
            raise ValueError('Invalid application status.')
        application = self.application_repository.get_by_id(application_id)
        if not application or application.get('recruiter_id') != str(recruiter_id):
            raise ValueError('Application not found.')
        if not self.application_repository.update(application_id, {'status': status}):
            raise ValueError('Could not update application status.')
        self.notifications.create_notification(
            application['candidate_id'], 'Application update',
            f'Your application status changed to {status}.',
        )
        self.audit.record(recruiter_id, 'application.status_updated', 'application', application_id, status)
        application['status'] = status
        return application

    def get_by_candidate(self, candidate_id):
        return self.application_repository.get_for_candidate(candidate_id)
