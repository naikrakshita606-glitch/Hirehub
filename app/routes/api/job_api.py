from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from app.services.audit_service import AuditService
from app.services.job_service import JobService
from app.repositories.application_repository import ApplicationRepository
from app.repositories.job_repository import JobRepository
from app.utils.decorators import api_role_required

job_api_bp = Blueprint('job_api', __name__)
job_service = JobService()


@job_api_bp.route('/jobs', methods=['GET'])
def list_jobs_api():
    jobs = job_service.list_jobs(
        query=request.args.get('q'),
        location=request.args.get('location'),
        job_type=request.args.get('type'),
        company=request.args.get('company'),
    )
    return jsonify({'jobs': [public_record(job) for job in jobs]})


@job_api_bp.route('/jobs', methods=['POST'])
@login_required
@api_role_required('recruiter')
def create_job_api():
    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        return jsonify({'error': 'JSON object required'}), 400
    payload['recruiter_id'] = current_user.id
    try:
        job = job_service.create_job(payload)
        AuditService().record(current_user.id, 'job.created', 'job', job['id'])
        return jsonify({'message': 'job created', 'job': public_record(job)}), 201
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400


@job_api_bp.route('/jobs/<job_id>', methods=['PATCH', 'DELETE'])
@login_required
@api_role_required('recruiter')
def manage_job_api(job_id):
    job = job_service.get_job(job_id)
    if not job or job.get('recruiter_id') != current_user.id:
        return jsonify({'error': 'job not found'}), 404
    if request.method == 'PATCH':
        payload = request.get_json(silent=True) or {}
        if not isinstance(payload, dict):
            return jsonify({'error': 'JSON object required'}), 400
        try:
            updated = job_service.update_job(job_id, current_user.id, payload)
            AuditService().record(current_user.id, 'job.updated', 'job', job_id)
            return jsonify({'job': public_record(updated)})
        except ValueError as exc:
            return jsonify({'error': str(exc)}), 400
    if ApplicationRepository().get_for_job(job_id):
        return jsonify({'error': 'jobs with applications cannot be deleted'}), 409
    if not JobRepository().delete(job_id):
        return jsonify({'error': 'could not delete job'}), 400
    AuditService().record(current_user.id, 'job.deleted', 'job', job_id)
    return jsonify({'message': 'job deleted'})


def public_record(record):
    return {key: value for key, value in record.items() if key != '_id'}
