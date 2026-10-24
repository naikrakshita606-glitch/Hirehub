from app.repositories.base_repository import BaseRepository


class ApplicationRepository(BaseRepository):
    collection_name = 'applications'

    def get_for_candidate(self, candidate_id):
        return [application for application in self.get_all() if application.get('candidate_id') == candidate_id]

    def get_for_job(self, job_id):
        return [application for application in self.get_all() if application.get('job_id') == job_id]

    def get_for_recruiter(self, recruiter_id):
        return [application for application in self.get_all() if application.get('recruiter_id') == recruiter_id]

    def get_by_candidate_and_job(self, candidate_id, job_id):
        return next(
            (application for application in self.get_all()
             if application.get('candidate_id') == candidate_id and application.get('job_id') == job_id),
            None,
        )
