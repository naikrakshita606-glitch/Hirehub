from flask import Blueprint, current_app, flash, redirect, render_template, request, send_from_directory, url_for
from flask_login import current_user, login_required

from app.repositories.interview_repository import InterviewRepository
from app.repositories.job_repository import JobRepository
from app.repositories.application_repository import ApplicationRepository
from app.repositories.user_repository import UserRepository
from app.services.audit_service import AuditService
from app.services.interview_service import InterviewService
from app.services.job_service import JobService
from app.services.notification_service import NotificationService
from app.utils.decorators import role_required

recruiter_bp = Blueprint('recruiter', __name__)
job_repo = JobRepository()
application_repo = ApplicationRepository()
job_service = JobService()
user_repo = UserRepository()
interview_repo = InterviewRepository()
interview_service = InterviewService()
notification_service = NotificationService()
audit_service = AuditService()


@recruiter_bp.route('/dashboard')
@login_required
@role_required('recruiter')
def dashboard():
    jobs = job_repo.get_for_recruiter(current_user.id)
    open_jobs = [job for job in jobs if job.get('status', 'published') == 'published']
    applications = application_repo.get_for_recruiter(current_user.id)
    interviews = [item for item in interview_repo.get_all() if item.get('recruiter_id') == current_user.id]
    notifications = notification_service.get_for_user(current_user.id)
    return render_template(
        'recruiter/dashboard.html', jobs=jobs, open_jobs=open_jobs, applications=applications,
        interviews=interviews, notifications=notifications,
    )


@recruiter_bp.route('/jobs', methods=['GET', 'POST'])
@login_required
@role_required('recruiter')
def jobs():
    if request.method == 'POST':
        payload = {
            'title': request.form.get('title', ''),
            'company': request.form.get('company', ''),
            'location': request.form.get('location', ''),
            'salary': request.form.get('salary', ''),
            'job_type': request.form.get('job_type', 'full-time'),
            'description': request.form.get('description', ''),
            'requirements': [item.strip() for item in request.form.get('requirements', '').split(',') if item.strip()],
            'recruiter_id': current_user.id,
        }
        try:
            created = job_service.create_job(payload)
            audit_service.record(current_user.id, 'job.created', 'job', created['id'])
        except ValueError as exc:
            flash(str(exc), 'danger')
            return redirect(url_for('recruiter.jobs'))
        flash('Job posted successfully.', 'success')
        return redirect(url_for('recruiter.jobs'))
    jobs = job_repo.get_for_recruiter(current_user.id)
    return render_template('recruiter/jobs.html', jobs=jobs)


@recruiter_bp.route('/applications')
@login_required
@role_required('recruiter')
def applications():
    applications = application_repo.get_for_recruiter(current_user.id)
    candidate_users = {user['id']: user for user in user_repo.get_all()}
    jobs = {job['id']: job for job in job_repo.get_for_recruiter(current_user.id)}
    interviews = interview_repo.get_all()
    interview_by_application = {item['application_id']: item for item in interviews if item.get('recruiter_id') == current_user.id}
    return render_template(
        'recruiter/applications.html', applications=applications,
        candidates=candidate_users, jobs=jobs, interviews=interview_by_application,
    )


@recruiter_bp.route('/applications/<application_id>/status', methods=['POST'])
@login_required
@role_required('recruiter')
def update_application_status(application_id):
    from app.services.application_service import ApplicationService

    try:
        ApplicationService().update_status(application_id, current_user.id, request.form.get('status', ''))
        flash('Application status updated.', 'success')
    except ValueError as exc:
        flash(str(exc), 'danger')
    return redirect(url_for('recruiter.applications'))


@recruiter_bp.route('/interviews', methods=['GET', 'POST'])
@login_required
@role_required('recruiter')
def interviews():
    if request.method == 'POST':
        try:
            scheduled = interview_service.schedule({
                'application_id': request.form.get('application_id'),
                'recruiter_id': current_user.id,
                'scheduled_at': request.form.get('scheduled_at', ''),
                'mode': request.form.get('mode', 'virtual'),
                'notes': request.form.get('notes', ''),
            })
            flash('Interview scheduled.', 'success')
        except ValueError as exc:
            flash(str(exc), 'danger')
    applications = application_repo.get_for_recruiter(current_user.id)
    jobs = {job['id']: job for job in job_repo.get_for_recruiter(current_user.id)}
    candidates = {user['id']: user for user in user_repo.get_all()}
    interviews = [item for item in interview_repo.get_all() if item.get('recruiter_id') == current_user.id]
    return render_template(
        'recruiter/interviews.html', applications=applications, jobs=jobs,
        candidates=candidates, interviews=interviews,
    )


@recruiter_bp.route('/interviews/<interview_id>', methods=['POST'])
@login_required
@role_required('recruiter')
def update_interview(interview_id):
    payload = {
        key: request.form[key]
        for key in ('scheduled_at', 'mode', 'notes', 'status')
        if key in request.form and request.form[key]
    }
    try:
        interview_service.update(interview_id, current_user.id, payload)
        flash('Interview updated.', 'success')
    except ValueError as exc:
        flash(str(exc), 'danger')
    return redirect(url_for('recruiter.interviews'))


@recruiter_bp.route('/jobs/<job_id>/delete', methods=['POST'])
@login_required
@role_required('recruiter')
def delete_job(job_id):
    job = job_repo.get_by_id(job_id)
    if not job or job.get('recruiter_id') != current_user.id:
        flash('Job not found.', 'danger')
    elif application_repo.get_for_job(job_id):
        flash('Jobs with applications cannot be deleted. Mark the job closed instead.', 'danger')
    elif job_repo.delete(job_id):
        audit_service.record(current_user.id, 'job.deleted', 'job', job_id)
        flash('Job deleted.', 'success')
    return redirect(url_for('recruiter.jobs'))


@recruiter_bp.route('/jobs/<job_id>/close', methods=['POST'])
@login_required
@role_required('recruiter')
def close_job(job_id):
    job = job_repo.get_by_id(job_id)
    if not job or job.get('recruiter_id') != current_user.id:
        flash('Job not found.', 'danger')
    else:
        job_repo.update(job_id, {'status': 'closed'})
        audit_service.record(current_user.id, 'job.closed', 'job', job_id)
        flash('Job closed.', 'success')
    return redirect(url_for('recruiter.jobs'))


@recruiter_bp.route('/jobs/<job_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('recruiter')
def edit_job(job_id):
    job = job_repo.get_by_id(job_id)
    if not job or job.get('recruiter_id') != current_user.id:
        flash('Job not found.', 'danger')
        return redirect(url_for('recruiter.jobs'))
    if request.method == 'POST':
        updates = {
            'title': request.form.get('title', '').strip(),
            'company': request.form.get('company', '').strip(),
            'location': request.form.get('location', '').strip(),
            'salary': request.form.get('salary', '').strip(),
            'job_type': request.form.get('job_type', 'full-time'),
            'description': request.form.get('description', '').strip(),
            'requirements': [item.strip() for item in request.form.get('requirements', '').split(',') if item.strip()],
        }
        try:
            job_service.update_job(job_id, current_user.id, updates)
            audit_service.record(current_user.id, 'job.updated', 'job', job_id)
            flash('Job updated.', 'success')
            return redirect(url_for('recruiter.jobs'))
        except ValueError as exc:
            flash(str(exc), 'danger')
    return render_template('recruiter/edit_job.html', job=job)


@recruiter_bp.route('/profile', methods=['GET', 'POST'])
@login_required
@role_required('recruiter')
def profile():
    if request.method == 'POST':
        updates = {
            'full_name': request.form.get('full_name', '').strip(),
            'phone': request.form.get('phone', '').strip(),
            'location': request.form.get('location', '').strip(),
        }
        if not updates['full_name']:
            flash('Name is required.', 'danger')
        else:
            user_repo.update_profile(current_user.id, updates)
            for field, value in updates.items():
                setattr(current_user, field, value)
            audit_service.record(current_user.id, 'recruiter.profile_updated', 'user', current_user.id)
            flash('Profile updated.', 'success')
    return render_template('recruiter/profile.html', user=current_user)


@recruiter_bp.route('/notifications')
@login_required
@role_required('recruiter')
def notifications():
    return render_template('candidate/notifications.html', notifications=notification_service.get_for_user(current_user.id))


@recruiter_bp.route('/notifications/<notification_id>/read', methods=['POST'])
@login_required
@role_required('recruiter')
def mark_notification_read(notification_id):
    if notification_service.mark_read(notification_id, current_user.id):
        flash('Notification marked as read.', 'success')
    else:
        flash('Notification not found.', 'danger')
    return redirect(url_for('recruiter.notifications'))


@recruiter_bp.route('/candidates/<candidate_id>/resume')
@login_required
@role_required('recruiter')
def candidate_resume(candidate_id):
    has_applied = any(
        application.get('candidate_id') == candidate_id
        for job in job_repo.get_for_recruiter(current_user.id)
        for application in application_repo.get_for_job(job['id'])
    )
    candidate = user_repo.get_by_id(candidate_id)
    if not has_applied or not candidate or not candidate.get('resume_filename'):
        return '', 404
    return send_from_directory(
        current_app.config['UPLOAD_FOLDER'],
        candidate['resume_filename'],
        as_attachment=True,
    )
