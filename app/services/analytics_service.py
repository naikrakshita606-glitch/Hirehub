from app.repositories.analytics_repository import AnalyticsRepository
from app.repositories.user_repository import UserRepository
from app.repositories.job_repository import JobRepository
from app.repositories.application_repository import ApplicationRepository


class AnalyticsService:
    def __init__(self):
        self.user_repository = UserRepository()
        self.job_repository = JobRepository()
        self.application_repository = ApplicationRepository()
        self.analytics_repository = AnalyticsRepository()

    def get_dashboard_metrics(self):
        users = self.user_repository.get_all()
        jobs = self.job_repository.get_all()
        applications = self.application_repository.get_all()
        metrics = self.analytics_repository.get_overview(users, jobs, applications)
        metrics['open_jobs'] = len([job for job in jobs if job.get('status', 'published') == 'published'])
        metrics['closed_jobs'] = len([job for job in jobs if job.get('status') == 'closed'])
        metrics['application_statuses'] = {
            status: len([application for application in applications if application.get('status') == status])
            for status in ('applied', 'reviewing', 'shortlisted', 'rejected', 'hired')
        }
        return metrics
