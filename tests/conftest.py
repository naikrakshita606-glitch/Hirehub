import pytest

from app import create_app


@pytest.fixture
def app(tmp_path):
    app = create_app({
        'MONGO_URI': 'mongodb://127.0.0.1:1',
        'MONGO_REQUIRED': False,
        'UPLOAD_FOLDER': str(tmp_path / 'resumes'),
    })
    app.config.update(TESTING=True, MONGO_AVAILABLE=False, SECRET_KEY='test-secret')
    yield app


@pytest.fixture
def client(app):
    return app.test_client()
