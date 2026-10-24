import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app
from app.extensions import mongo


app = create_app()

with app.app_context():
    if not app.config.get('MONGO_AVAILABLE'):
        raise RuntimeError('MongoDB is required to create HireHub indexes.')

    db = mongo.get_db()
    db.users.create_index('email', unique=True, name='users_email_unique')
    db.jobs.create_index(
        [('status', 1), ('location', 1), ('job_type', 1)],
        name='jobs_public_search',
    )
    db.jobs.create_index([('recruiter_id', 1), ('status', 1)], name='jobs_by_recruiter')
    db.applications.create_index(
        [('candidate_id', 1), ('job_id', 1)],
        unique=True,
        name='applications_candidate_job_unique',
    )
    db.applications.create_index(
        [('recruiter_id', 1), ('status', 1)],
        name='applications_by_recruiter',
    )
    db.interviews.create_index([('candidate_id', 1), ('scheduled_at', 1)], name='interviews_by_candidate')
    db.interviews.create_index([('recruiter_id', 1), ('scheduled_at', 1)], name='interviews_by_recruiter')
    db.notifications.create_index(
        [('user_id', 1), ('is_read', 1), ('created_at', -1)],
        name='notifications_by_user',
    )
    db.audit_logs.create_index([('created_at', -1)], name='audit_logs_recent')
    print(f"Indexes created for MongoDB database '{db.name}'.")
