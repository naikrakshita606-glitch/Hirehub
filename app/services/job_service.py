import uuid

from app.repositories.job_repository import JobRepository


class JobService:
    def __init__(self):
        self.job_repository = JobRepository()

    def create_job(self, payload):
        title_value = payload.get('title', '')
        company_value = payload.get('company', '')
        description_value = payload.get('description', '')
        if not all(isinstance(value, str) for value in (title_value, company_value, description_value)):
            raise ValueError('Title, company, and description must be text.')
        title = title_value.strip()
        company = company_value.strip()
        description = description_value.strip()
        if not title or not company or not description:
            raise ValueError('Title, company, and description are required.')
        job_type = payload.get('job_type', 'full-time')
        if not isinstance(job_type, str) or job_type not in {'full-time', 'part-time', 'contract'}:
            raise ValueError('Select a valid job type.')
        requirements = payload.get('requirements', [])
        if isinstance(requirements, str):
            requirements = [item.strip() for item in requirements.split(',') if item.strip()]
        if not isinstance(requirements, list) or any(not isinstance(item, str) for item in requirements):
            raise ValueError('Requirements must be a list of text values.')
        job = {
            'id': str(uuid.uuid4()),
            'title': title,
            'company': company,
            'location': payload.get('location', '').strip() if isinstance(payload.get('location', ''), str) else '',
            'salary': payload.get('salary', '').strip() if isinstance(payload.get('salary', ''), str) else '',
            'job_type': job_type,
            'description': description,
            'requirements': requirements,
            'recruiter_id': payload.get('recruiter_id', ''),
            'status': 'published',
        }
        return self.job_repository.create(job)

    def list_jobs(self, query=None, location=None, job_type=None, company=None):
        return self.job_repository.search(query=query, location=location, job_type=job_type, company=company)

    def update_job(self, job_id, recruiter_id, payload):
        job = self.job_repository.get_by_id(job_id)
        if not job or job.get('recruiter_id') != str(recruiter_id):
            raise ValueError('Job not found.')
        updates = {
            key: payload[key] for key in
            ('title', 'company', 'location', 'salary', 'job_type', 'description', 'requirements', 'status')
            if key in payload
        }
        for key in ('title', 'company', 'location', 'salary', 'job_type', 'description'):
            if key in updates:
                if not isinstance(updates[key], str):
                    raise ValueError(f'{key.replace("_", " ").title()} must be text.')
                updates[key] = updates[key].strip()
        if 'job_type' in updates and updates['job_type'] not in {'full-time', 'part-time', 'contract'}:
            raise ValueError('Select a valid job type.')
        if ('title' in updates and not updates['title']) or ('company' in updates and not updates['company']):
            raise ValueError('Title and company cannot be empty.')
        if 'description' in updates and not updates['description']:
            raise ValueError('Description cannot be empty.')
        if 'status' in updates:
            if not isinstance(updates['status'], str) or updates['status'] not in {'published', 'closed'}:
                raise ValueError('Invalid job status.')
        if 'requirements' in updates and isinstance(updates['requirements'], str):
            updates['requirements'] = [item.strip() for item in updates['requirements'].split(',') if item.strip()]
        if 'requirements' in updates and (
            not isinstance(updates['requirements'], list)
            or any(not isinstance(item, str) for item in updates['requirements'])
        ):
            raise ValueError('Requirements must be a list of text values.')
        if updates and not self.job_repository.update(job_id, updates):
            updated = self.job_repository.get_by_id(job_id)
            if not updated or any(updated.get(key) != value for key, value in updates.items()):
                raise ValueError('Could not update job.')
        return self.job_repository.get_by_id(job_id)

    def get_job(self, job_id):
        return self.job_repository.get_by_id(job_id)
