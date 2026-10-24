from datetime import datetime, timedelta, timezone
from io import BytesIO

from app.repositories.application_repository import ApplicationRepository
from app.repositories.interview_repository import InterviewRepository
from app.repositories.job_repository import JobRepository
from app.repositories.user_repository import UserRepository


def register(client, email, role):
    return client.post('/register', data={
        'full_name': email.split('@')[0],
        'email': email,
        'password': 'secret123',
        'role': role,
    }, follow_redirects=True)


def test_candidate_and_recruiter_can_track_application_and_schedule_interview(app):
    recruiter = app.test_client()
    register(recruiter, 'recruiter-flow@example.com', 'recruiter')
    recruiter.post('/recruiter/jobs', data={
        'title': 'Backend Engineer',
        'company': 'HireHub',
        'description': 'Build APIs',
        'requirements': 'Python, Flask',
    })
    assert recruiter.get('/recruiter/notifications').status_code == 200

    with app.app_context():
        job = JobRepository().get_all()[0]

    candidate = app.test_client()
    register(candidate, 'candidate-flow@example.com', 'candidate')
    response = candidate.post(f"/candidate/apply/{job['id']}", data={'cover_letter': 'Interested'})
    assert response.status_code == 302
    recruiter_notifications = recruiter.get('/recruiter/notifications')
    assert recruiter_notifications.status_code == 200
    assert b'/recruiter/notifications/' in recruiter_notifications.data

    with app.app_context():
        application = ApplicationRepository().get_all()[0]
        assert application['status'] == 'applied'

    status_response = recruiter.post(
        f"/recruiter/applications/{application['id']}/status",
        data={'status': 'shortlisted'},
    )
    assert status_response.status_code == 302
    interview_response = recruiter.post('/recruiter/interviews', data={
        'application_id': application['id'],
        'scheduled_at': (datetime.now(timezone.utc) + timedelta(days=2)).isoformat(),
        'mode': 'virtual',
        'notes': 'Video call',
    })
    assert interview_response.status_code == 200
    assert b'Interview scheduled.' in interview_response.data
    with app.app_context():
        interview = InterviewRepository().get_all()[0]
    interview_update = recruiter.patch(
        f"/api/interviews/{interview['id']}",
        json={'status': 'cancelled'},
    )
    assert interview_update.status_code == 200
    assert interview_update.get_json()['interview']['status'] == 'cancelled'

    candidate_response = candidate.get('/candidate/applications')
    assert b'shortlisted' in candidate_response.data
    assert candidate.get('/candidate/interviews').status_code == 200
    assert candidate.get('/candidate/notifications').status_code == 200


def test_resume_upload_and_download_are_limited_to_owner(app):
    candidate = app.test_client()
    register(candidate, 'resume-owner@example.com', 'candidate')
    upload_response = candidate.post('/candidate/profile', data={
        'full_name': 'Resume Owner',
        'phone': '',
        'location': 'Remote',
        'skills': 'Python',
        'experience': '2 years',
        'summary': 'Engineer',
        'resume': (BytesIO(b'%PDF-1.4 test content'), 'resume.pdf'),
    }, content_type='multipart/form-data')
    assert upload_response.status_code == 200

    with app.app_context():
        owner = UserRepository().get_by_email('resume-owner@example.com')
        filename = owner['resume_filename']

    assert candidate.get(f'/candidate/resume/{filename}').status_code == 200
    other = app.test_client()
    register(other, 'resume-other@example.com', 'candidate')
    assert other.get(f'/candidate/resume/{filename}').status_code == 404


def test_resume_rest_upload_and_download(client):
    register(client, 'api-resume@example.com', 'candidate')
    upload = client.post(
        '/api/profile/resume',
        data={'resume': (BytesIO(b'%PDF-1.4 API test'), 'api-resume.pdf')},
        content_type='multipart/form-data',
    )
    assert upload.status_code == 201
    assert upload.get_json()['filename'].endswith('.pdf')
    download = client.get('/api/profile/resume')
    assert download.status_code == 200
    assert download.data.startswith(b'%PDF-1.4')


def test_api_authentication_and_role_authorization(client):
    response = client.post('/api/jobs', json={
        'title': 'Unauthorized',
        'company': 'Nope',
        'description': 'Must be rejected',
    })
    assert response.status_code == 401
    assert response.get_json()['error'] == 'authentication required'

    register(client, 'api-candidate@example.com', 'candidate')
    forbidden = client.post('/api/jobs', json={
        'title': 'Unauthorized',
        'company': 'Nope',
        'description': 'Must be rejected',
    })
    assert forbidden.status_code == 403
    assert forbidden.get_json()['error'] == 'forbidden'


def test_api_login_creates_and_logout_clears_session(client):
    registered = client.post('/api/auth/register', json={
        'full_name': 'API Candidate',
        'email': 'api-session@example.com',
        'password': 'secret123',
        'role': 'candidate',
    })
    assert registered.status_code == 201
    assert 'password_hash' not in registered.get_json()['user']

    login = client.post('/api/auth/login', json={
        'email': 'api-session@example.com',
        'password': 'secret123',
    })
    assert login.status_code == 200
    assert 'hirehub_role=candidate' in login.headers.get('Set-Cookie', '')
    assert client.get('/api/auth/me').get_json()['user']['role'] == 'candidate'

    logout = client.post('/api/auth/logout')
    assert logout.status_code == 200
    assert 'hirehub_role=;' in logout.headers.get('Set-Cookie', '')
    assert client.get('/api/auth/me').status_code == 401


def test_rest_role_workflows_for_profiles_jobs_applications_and_interviews(app):
    recruiter = app.test_client()
    register(recruiter, 'rest-recruiter@example.com', 'recruiter')
    job_response = recruiter.post('/api/jobs', json={
        'title': 'REST Platform Engineer',
        'company': 'HireHub API',
        'location': 'Remote',
        'job_type': 'full-time',
        'description': 'Build reliable APIs',
        'requirements': ['Python', 'Flask'],
    })
    assert job_response.status_code == 201
    job_id = job_response.get_json()['job']['id']
    assert recruiter.patch(f'/api/jobs/{job_id}', json={'salary': '$120k'}).status_code == 200
    assert app.test_client().get('/api/jobs?q=REST+Platform').status_code == 200

    candidate = app.test_client()
    register(candidate, 'rest-candidate@example.com', 'candidate')
    profile_response = candidate.put('/api/profile', json={
        'full_name': 'REST Candidate',
        'location': 'Remote',
        'skills': ['Python', 'Flask'],
        'experience': '3 years',
        'summary': 'API test profile',
    })
    assert profile_response.status_code == 200
    assert 'password_hash' not in profile_response.get_json()['user']

    apply_response = candidate.post('/api/applications', json={
        'job_id': job_id,
        'cover_letter': 'API application',
    })
    assert apply_response.status_code == 201
    application_id = apply_response.get_json()['application']['id']
    assert candidate.get('/api/applications').get_json()['applications'][0]['id'] == application_id
    assert recruiter.get('/api/applications').get_json()['applications'][0]['id'] == application_id

    status_response = recruiter.patch(
        f'/api/applications/{application_id}/status',
        json={'status': 'reviewing'},
    )
    assert status_response.status_code == 200
    assert candidate.get('/api/notifications').get_json()['notifications']

    scheduled_at = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()
    interview_response = recruiter.post('/api/interviews', json={
        'application_id': application_id,
        'scheduled_at': scheduled_at,
        'mode': 'virtual',
        'notes': 'REST interview',
    })
    assert interview_response.status_code == 201
    interview_id = interview_response.get_json()['interview']['id']
    assert candidate.get('/api/interviews').get_json()['interviews'][0]['id'] == interview_id
    assert recruiter.patch(f'/api/interviews/{interview_id}', json={
        'status': 'cancelled',
    }).status_code == 200

    assert candidate.get('/api/recommendations').get_json()['jobs']
    notifications = candidate.get('/api/notifications').get_json()['notifications']
    notification_id = notifications[0]['id']
    assert candidate.post(f'/api/notifications/{notification_id}/read').status_code == 200

    admin = app.test_client()
    assert admin.post('/login', data={
        'email': 'admin@hirehub.local',
        'password': 'admin123',
    }).status_code == 302
    assert admin.get('/api/reports').status_code == 200
    assert admin.get('/api/audit-logs').status_code == 200
    role_response = admin.patch(
        f"/api/users/{profile_response.get_json()['user']['id']}/role",
        json={'role': 'recruiter'},
    )
    assert role_response.status_code == 200


def test_admin_tools_and_recruiter_pages_render(app):
    recruiter = app.test_client()
    register(recruiter, 'recruiter-pages@example.com', 'recruiter')
    recruiter.post('/recruiter/jobs', data={
        'title': 'QA Engineer',
        'company': 'HireHub',
        'description': 'Test application flows',
    })
    with app.app_context():
        job = JobRepository().get_all()[0]

    for path in (
        '/recruiter/jobs',
        '/recruiter/applications',
        '/recruiter/interviews',
        f"/recruiter/jobs/{job['id']}/edit",
        '/recruiter/profile',
        '/jobs',
    ):
        assert recruiter.get(path).status_code == 200

    admin = app.test_client()
    login = admin.post('/login', data={
        'email': 'admin@hirehub.local',
        'password': 'admin123',
    })
    assert login.status_code == 302
    for path in (
        '/admin/dashboard',
        '/admin/users',
        '/admin/reports',
        '/admin/audit-logs',
        '/admin/profile',
        '/dashboard/overview',
    ):
        assert admin.get(path).status_code == 200
    assert admin.get('/api/analytics/overview').status_code == 200
    export = admin.get('/admin/reports/export.csv')
    assert export.status_code == 200
    assert export.mimetype == 'text/csv'
    assert b'application_statuses' in export.data
    assert admin.get('/api/reports').status_code == 200
    assert admin.get('/api/audit-logs?limit=5').status_code == 200


def test_logout_clears_authenticated_session(client):
    register(client, 'logout@example.com', 'candidate')
    assert client.get('/dashboard').status_code == 302
    response = client.post('/logout')
    assert response.status_code == 302
    assert response.headers.get('Set-Cookie', '').find('hirehub_role=;') >= 0
    assert client.get('/candidate/dashboard').status_code == 302


def test_candidate_dashboard_shows_open_jobs_without_skill_match(app):
    recruiter = app.test_client()
    register(recruiter, 'fallback-recruiter@example.com', 'recruiter')
    recruiter.post('/recruiter/jobs', data={
        'title': 'Data Analyst',
        'company': 'HireHub',
        'description': 'Analyze product metrics',
        'requirements': 'SQL, Tableau',
    })

    candidate = app.test_client()
    register(candidate, 'fallback-candidate@example.com', 'candidate')
    dashboard = candidate.get('/candidate/dashboard')
    assert dashboard.status_code == 200
    assert b'Open jobs' in dashboard.data
    assert b'Data Analyst' in dashboard.data
    assert candidate.get('/candidate/jobs').status_code == 200
