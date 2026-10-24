from app.repositories.base_repository import BaseRepository


class JobRepository(BaseRepository):
    collection_name = 'jobs'

    def search(self, query=None, location=None, job_type=None, company=None, status='published'):
        results = self.get_all()
        if status:
            results = [job for job in results if job.get('status', 'published') == status]
        if query:
            q = query.lower()
            results = [
                job for job in results
                if q in job.get('title', '').lower()
                or q in job.get('company', '').lower()
                or q in job.get('description', '').lower()
                or any(q in str(skill).lower() for skill in job.get('requirements', []))
            ]
        if location:
            loc = location.lower()
            results = [job for job in results if loc in job.get('location', '').lower()]
        if job_type:
            type_name = job_type.lower()
            results = [job for job in results if job.get('job_type', '').lower() == type_name]
        if company:
            company_name = company.lower()
            results = [job for job in results if company_name in job.get('company', '').lower()]
        return results

    def get_for_recruiter(self, recruiter_id):
        return [job for job in self.get_all() if job.get('recruiter_id') == recruiter_id]
