def test_candidate_can_apply(client):
    client.post('/register', data={
        'full_name': 'Candidate One',
        'email': 'candidate@example.com',
        'password': 'secret123',
        'role': 'candidate',
        'phone': '9999',
        'location': 'Delhi',
        'skills': 'Python'
    }, follow_redirects=True)
    client.post('/login', data={
        'email': 'candidate@example.com',
        'password': 'secret123'
    }, follow_redirects=True)

    response = client.get('/jobs')
    assert response.status_code == 200
