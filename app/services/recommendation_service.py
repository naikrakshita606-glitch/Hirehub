from app.repositories.job_repository import JobRepository


class RecommendationService:
    def __init__(self):
        self.jobs = JobRepository()

    def for_candidate(self, candidate, limit=10):
        skills = {str(skill).strip().lower() for skill in candidate.get('skills', []) if str(skill).strip()}
        location = str(candidate.get('location', '')).strip().lower()
        scored_jobs = []
        for job in self.jobs.search():
            requirements = {str(skill).strip().lower() for skill in job.get('requirements', [])}
            score = len(skills & requirements)
            if location and location in str(job.get('location', '')).lower():
                score += 1
            if score:
                scored_jobs.append((score, job))
        scored_jobs.sort(key=lambda item: (item[0], item[1].get('title', '').lower()), reverse=True)
        return [job for _, job in scored_jobs[:limit]]
