from flask import Blueprint, render_template, request

from app.repositories.job_repository import JobRepository

job_bp = Blueprint('jobs', __name__)
job_repo = JobRepository()


@job_bp.route('/jobs')
def list_jobs():
    query = request.args.get('q', '')
    location = request.args.get('location', '')
    job_type = request.args.get('type', '')
    company = request.args.get('company', '')
    jobs = job_repo.search(query=query, location=location, job_type=job_type, company=company)
    return render_template(
        'jobs/list.html', jobs=jobs, query=query,
        location=location, job_type=job_type, company=company,
    )


@job_bp.route('/job/<job_id>')
def job_detail(job_id):
    job = job_repo.get_by_id(job_id)
    if not job:
        return render_template('errors/404.html'), 404
    return render_template('jobs/detail.html', job=job)
