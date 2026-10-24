import os
import uuid

from flask import Blueprint, current_app, jsonify, request, send_from_directory, session
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.utils import secure_filename

from app.models.user import User
from app.repositories.application_repository import ApplicationRepository
from app.repositories.job_repository import JobRepository
from app.repositories.user_repository import UserRepository
from app.services.audit_service import AuditService
from app.services.auth_service import AuthService
from app.services.notification_service import NotificationService
from app.services.recommendation_service import RecommendationService
from app.utils.decorators import api_role_required

auth_api_bp = Blueprint('auth_api', __name__)
auth_service = AuthService()


@auth_api_bp.route('/auth/register', methods=['POST'])
def register_api():
    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        return jsonify({'error': 'JSON object required'}), 400
    try:
        user = auth_service.register(payload)
        AuditService().record(user['id'], 'user.registered', 'user', user['id'])
        return jsonify({'message': 'registered', 'user': public_user(user)}), 201
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400


@auth_api_bp.route('/auth/login', methods=['POST'])
def login_api():
    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        return jsonify({'error': 'JSON object required'}), 400
    user = auth_service.login(data.get('email', ''), data.get('password', ''))
    if user:
        session.clear()
        login_user(User.from_dict(user))
        session.permanent = True
        session['role'] = user.get('role')
        AuditService().record(user['id'], 'user.logged_in', 'user', user['id'])
        response = jsonify({'message': 'logged in', 'user': public_user(user)})
        response.set_cookie(
            'hirehub_role',
            user.get('role'),
            httponly=True,
            secure=current_app.config['SESSION_COOKIE_SECURE'],
            samesite='Lax',
        )
        return response, 200
    return jsonify({'error': 'invalid credentials'}), 401


@auth_api_bp.route('/auth/me', methods=['GET'])
@login_required
def current_session():
    return jsonify({'user': {
        'id': current_user.id,
        'email': current_user.email,
        'role': current_user.role,
        'full_name': current_user.full_name,
    }})


@auth_api_bp.route('/auth/logout', methods=['POST'])
@login_required
def logout_api():
    AuditService().record(current_user.get_id(), 'user.logged_out', 'user', current_user.get_id())
    logout_user()
    session.clear()
    response = jsonify({'message': 'logged out'})
    response.delete_cookie('hirehub_role')
    return response


@auth_api_bp.route('/profile', methods=['GET', 'PUT'])
@login_required
def profile_api():
    repository = UserRepository()
    if request.method == 'PUT':
        data = request.get_json(silent=True) or {}
        if not isinstance(data, dict):
            return jsonify({'error': 'JSON object required'}), 400
        updates = {
            key: data[key] for key in ('full_name', 'phone', 'location', 'skills', 'experience', 'summary')
            if key in data
        }
        if 'skills' in updates and not isinstance(updates['skills'], list):
            return jsonify({'error': 'skills must be a list'}), 400
        repository.update_profile(current_user.id, updates)
        for key, value in updates.items():
            setattr(current_user, key, value)
        AuditService().record(current_user.id, 'user.profile_updated', 'user', current_user.id)
    user = repository.get_by_id(current_user.id)
    return jsonify({'user': public_user(user)})


@auth_api_bp.route('/profile/resume', methods=['GET', 'POST'])
@login_required
@api_role_required('candidate')
def profile_resume_api():
    if request.method == 'POST':
        resume = request.files.get('resume')
        if not resume or not resume.filename:
            return jsonify({'error': 'resume file is required'}), 400
        extension = os.path.splitext(secure_filename(resume.filename))[1].lower()
        if extension not in {'.pdf', '.doc', '.docx'}:
            return jsonify({'error': 'upload a PDF, DOC, or DOCX resume'}), 400
        os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
        filename = f'{uuid.uuid4().hex}{extension}'
        resume.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
        previous_filename = current_user.resume_filename
        if not UserRepository().update_profile(current_user.id, {'resume_filename': filename}):
            user = UserRepository().get_by_id(current_user.id)
            if not user:
                os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                return jsonify({'error': 'user not found'}), 404
        current_user.resume_filename = filename
        if previous_filename:
            old_path = os.path.join(current_app.config['UPLOAD_FOLDER'], previous_filename)
            if os.path.isfile(old_path):
                os.remove(old_path)
        AuditService().record(current_user.id, 'candidate.resume_uploaded', 'user', current_user.id)
        return jsonify({'message': 'resume uploaded', 'filename': filename}), 201
    if not current_user.resume_filename:
        return jsonify({'error': 'no resume uploaded'}), 404
    return send_from_directory(
        current_app.config['UPLOAD_FOLDER'],
        current_user.resume_filename,
        as_attachment=True,
    )


@auth_api_bp.route('/candidates/<candidate_id>/resume', methods=['GET'])
@login_required
@api_role_required('recruiter')
def candidate_resume_api(candidate_id):
    candidate = UserRepository().get_by_id(candidate_id)
    recruiter_jobs = JobRepository().get_for_recruiter(current_user.id)
    has_applied = any(
        application.get('candidate_id') == candidate_id
        for job in recruiter_jobs
        for application in ApplicationRepository().get_for_job(job['id'])
    )
    if not candidate or not candidate.get('resume_filename') or not has_applied:
        return jsonify({'error': 'resume not found'}), 404
    AuditService().record(current_user.id, 'candidate.resume_downloaded', 'user', candidate_id)
    return send_from_directory(
        current_app.config['UPLOAD_FOLDER'],
        candidate['resume_filename'],
        as_attachment=True,
    )


@auth_api_bp.route('/recommendations', methods=['GET'])
@login_required
@api_role_required('candidate')
def recommendations_api():
    jobs = RecommendationService().for_candidate({
        'skills': current_user.skills,
        'location': current_user.location,
    })
    return jsonify({'jobs': [{key: value for key, value in job.items() if key != '_id'} for job in jobs]})


@auth_api_bp.route('/notifications', methods=['GET'])
@login_required
def notifications_api():
    notifications = NotificationService().get_for_user(current_user.id)
    return jsonify({'notifications': [{key: value for key, value in item.items() if key != '_id'} for item in notifications]})


@auth_api_bp.route('/notifications/<notification_id>/read', methods=['POST'])
@login_required
def mark_notification_read_api(notification_id):
    if not NotificationService().mark_read(notification_id, current_user.id):
        return jsonify({'error': 'notification not found'}), 404
    return jsonify({'message': 'notification marked as read'})


@auth_api_bp.route('/users/<user_id>/role', methods=['PATCH'])
@login_required
@api_role_required('admin')
def update_user_role_api(user_id):
    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        return jsonify({'error': 'JSON object required'}), 400
    role = data.get('role')
    if not isinstance(role, str) or role not in {'candidate', 'recruiter', 'admin'}:
        return jsonify({'error': 'invalid role'}), 400
    if user_id == current_user.id and role != 'admin':
        return jsonify({'error': 'cannot remove your own admin role'}), 400
    repository = UserRepository()
    if not repository.update(user_id, {'role': role}):
        user = repository.get_by_id(user_id)
        if not user or user.get('role') != role:
            return jsonify({'error': 'user not found'}), 404
    AuditService().record(current_user.id, 'admin.user_role_updated', 'user', user_id, role)
    return jsonify({'message': 'role updated', 'user_id': user_id, 'role': role})


def public_user(user):
    return {key: value for key, value in user.items() if key not in {'password_hash', '_id'}}
