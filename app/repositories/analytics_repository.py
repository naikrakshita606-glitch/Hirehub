from app.repositories.base_repository import BaseRepository


class AnalyticsRepository(BaseRepository):
    collection_name = 'analytics'

    def get_overview(self, users, jobs, applications):
        return {
            'total_users': len(users),
            'total_jobs': len(jobs),
            'total_applications': len(applications),
            'candidate_count': len([u for u in users if u.get('role') == 'candidate']),
            'recruiter_count': len([u for u in users if u.get('role') == 'recruiter']),
            'admin_count': len([u for u in users if u.get('role') == 'admin']),
        }
