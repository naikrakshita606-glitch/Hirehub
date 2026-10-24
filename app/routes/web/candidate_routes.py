import os
import uuid

from flask import Blueprint, current_app, flash, redirect, render_template, request, send_from_directory, url_for
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

from app.repositories.interview_repository import InterviewRepository
from app.repositories.job_repository import JobRepository
from app.repositories.application_repository import ApplicationRepository
from app.repositories.user_repository import UserRepository
from app.services.application_service import ApplicationService
from app.services.audit_service import AuditService
from app.services.notification_service import NotificationService
from app.services.recommendation_service import RecommendationService
from app.utils.decorators import role_required

candidate_bp = Blueprint('candidate', __name__)
job_repo = JobRepository()
application_repo = ApplicationRepository()
application_service = ApplicationService()
user_repo = UserRepository()
interview_repo = InterviewRepository()
notification_service = NotificationService()
audit_service = AuditService()
recommendation_service = RecommendationService()


@candidate_bp.route('/dashboard')
@login_required
@role_required('candidate')
def dashboard():
    jobs = job_repo.search()
    applications = application_repo.get_for_candidate(current_user.id)
    interviews = [item for item in interview_repo.get_all() if item.get('candidate_id') == current_user.id]
    recommendations = recommendation_service.for_candidate(current_user.to_dict() if hasattr(current_user, 'to_dict') else {
        'skills': current_user.skills, 'location': current_user.location,
    })
    notifications = notification_service.get_for_user(current_user.id)
    return render_template(
        'candidate/dashboard.html', jobs=jobs, applications=applications, interviews=interviews,
        recommendations=recommendations, notifications=notifications,
    )


@candidate_bp.route('/profile', methods=['GET', 'POST'])
@login_required
@role_required('candidate')
def profile():
    if request.method == 'POST':
        updates = {
            'full_name': request.form.get('full_name', '').strip(),
            'phone': request.form.get('phone', '').strip(),
            'location': request.form.get('location', '').strip(),
            'skills': [item.strip() for item in request.form.get('skills', '').split(',') if item.strip()],
            'experience': request.form.get('experience', '').strip(),
            'summary': request.form.get('summary', '').strip(),
        }
        resume = request.files.get('resume')
        previous_resume = current_user.resume_filename
        if resume and resume.filename:
            original_name = secure_filename(resume.filename)
            extension = os.path.splitext(original_name)[1].lower()
            if extension not in {'.pdf', '.doc', '.docx'}:
                flash('Upload a PDF, DOC, or DOCX resume.', 'danger')
                return render_template('candidate/profile.html', user=current_user)
            os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
            filename = f'{uuid.uuid4().hex}{extension}'
            resume.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
            updates['resume_filename'] = filename
        if not user_repo.update_profile(current_user.id, updates):
            persisted_user = user_repo.get_by_id(current_user.id)
            if not persisted_user:
                if 'resume_filename' in updates:
                    os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], updates['resume_filename']))
                flash('Could not save profile. Please try again.', 'danger')
                return render_template('candidate/profile.html', user=current_user)
        for field, value in updates.items():
            setattr(current_user, field, value)
        if previous_resume and 'resume_filename' in updates and previous_resume != updates['resume_filename']:
            old_path = os.path.join(current_app.config['UPLOAD_FOLDER'], previous_resume)
            if os.path.isfile(old_path):
                os.remove(old_path)
        audit_service.record(current_user.id, 'candidate.profile_updated', 'user', current_user.id)
        flash('Profile updated successfully.', 'success')
    return render_template('candidate/profile.html', user=current_user)


@candidate_bp.route('/jobs')
@login_required
@role_required('candidate')
def jobs():
    query = request.args.get('q', '')
    location = request.args.get('location', '')
    job_type = request.args.get('type', '')
    company = request.args.get('company', '')
    jobs = job_repo.search(query=query, location=location, job_type=job_type, company=company)
    return render_template('candidate/jobs.html', jobs=jobs, query=query, location=location, job_type=job_type, company=company)


@candidate_bp.route('/apply/<job_id>', methods=['POST'])
@login_required
@role_required('candidate')
def apply(job_id):
    try:
        application_service.apply({
            'job_id': job_id,
            'candidate_id': current_user.id,
            'cover_letter': request.form.get('cover_letter', ''),
        })
        flash('Application submitted successfully.', 'success')
    except ValueError as exc:
        flash(str(exc), 'danger')
    return redirect(url_for('candidate.dashboard'))


@candidate_bp.route('/applications')
@login_required
@role_required('candidate')
def applications():
    applications = application_repo.get_for_candidate(current_user.id)
    jobs = {job['id']: job for job in job_repo.get_all()}
    return render_template('candidate/applications.html', applications=applications, jobs=jobs)


@candidate_bp.route('/resume/<filename>')
@login_required
@role_required('candidate')
def view_resume(filename):
    if filename != current_user.resume_filename:
        return '', 404
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename, as_attachment=True)


@candidate_bp.route('/recommendations')
@login_required
@role_required('candidate')
def recommendations():
    candidate = {'skills': current_user.skills, 'location': current_user.location}
    jobs = recommendation_service.for_candidate(candidate) or job_repo.search()
    return render_template('candidate/jobs.html', jobs=jobs, query='', location='', job_type='', company='')


@candidate_bp.route('/interviews')
@login_required
@role_required('candidate')
def interviews():
    items = [item for item in interview_repo.get_all() if item.get('candidate_id') == current_user.id]
    return render_template('candidate/interviews.html', interviews=items)


@candidate_bp.route('/notifications')
@login_required
@role_required('candidate')
def notifications():
    return render_template('candidate/notifications.html', notifications=notification_service.get_for_user(current_user.id))


@candidate_bp.route('/notifications/<notification_id>/read', methods=['POST'])
@login_required
@role_required('candidate')
def mark_notification_read(notification_id):
    if notification_service.mark_read(notification_id, current_user.id):
        flash('Notification marked as read.', 'success')
    else:
        flash('Notification not found.', 'danger')
    return redirect(url_for('candidate.notifications'))
