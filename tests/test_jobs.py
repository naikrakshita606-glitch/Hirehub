def test_recruiter_can_post_job(client):
    client.post('/register', data={
        'full_name': 'Recruiter One',
        'email': 'recruiter@example.com',
        'password': 'secret123',
        'role': 'recruiter',
        'phone': '123456',
        'location': 'Pune',
        'skills': 'Hiring'
    }, follow_redirects=True)

    client.post('/login', data={
        'email': 'recruiter@example.com',
        'password': 'secret123'
    }, follow_redirects=True)

    response = client.post('/recruiter/jobs', data={
        'title': 'Python Developer',
        'company': 'HireHub',
        'location': 'Remote',
        'salary': '$120k',
        'job_type': 'full-time',
        'description': 'Build production APIs.',
        'requirements': 'Python, Flask'
    }, follow_redirects=True)

    assert response.status_code == 200
