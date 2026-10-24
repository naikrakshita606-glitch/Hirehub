def test_user_can_register_and_login(client):
    response = client.post('/register', data={
        'full_name': 'Jane Doe',
        'email': 'jane@example.com',
        'password': 'secret123',
        'role': 'candidate',
        'phone': '123456',
        'location': 'Bengaluru',
        'skills': 'Python, Flask'
    }, follow_redirects=True)
    assert response.status_code == 200

    login_response = client.post('/login', data={
        'email': 'jane@example.com',
        'password': 'secret123'
    }, follow_redirects=True)
    assert login_response.status_code == 200


def test_default_admin_can_log_in(client):
    response = client.post('/login', data={
        'email': 'admin@hirehub.local',
        'password': 'admin123',
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Admin dashboard' in response.data


def test_public_registration_cannot_create_admin(client):
    response = client.post('/register', data={
        'full_name': 'Unauthorized Admin',
        'email': 'unauthorized@example.com',
        'password': 'secret123',
        'role': 'admin',
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Only candidate and recruiter accounts can be registered.' in response.data
