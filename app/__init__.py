import os
from flask import Flask, jsonify, redirect, render_template, request, url_for
from pymongo.errors import PyMongoError

from app.config import Config
from app.extensions import bcrypt, login_manager, mongo


def create_app(config_object=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)
    if config_object:
        if isinstance(config_object, dict):
            app.config.from_mapping(config_object)
        else:
            app.config.from_object(config_object)

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    bcrypt.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    @login_manager.unauthorized_handler
    def unauthorized():
        if request.path.startswith('/api/'):
            return jsonify({'error': 'authentication required'}), 401
        return redirect(url_for('auth.login'))

    mongo.init_app(app)

    if app.config.get('DEFAULT_ADMIN_PASSWORD'):
        from app.services.auth_service import AuthService

        with app.app_context():
            AuthService().seed_admin(
                email=app.config['DEFAULT_ADMIN_EMAIL'],
                password=app.config['DEFAULT_ADMIN_PASSWORD'],
            )

    @login_manager.user_loader
    def load_user(user_id):
        from app.repositories.user_repository import UserRepository
        from app.models.user import User

        user_data = UserRepository().get_by_id(user_id)
        if user_data:
            return User.from_dict(user_data)
        return None

    from app.routes.web.auth_routes import auth_bp
    from app.routes.web.dashboard_routes import dashboard_bp
    from app.routes.web.candidate_routes import candidate_bp
    from app.routes.web.recruiter_routes import recruiter_bp
    from app.routes.web.admin_routes import admin_bp
    from app.routes.web.job_routes import job_bp
    from app.routes.api.auth_api import auth_api_bp
    from app.routes.api.job_api import job_api_bp
    from app.routes.api.application_api import application_api_bp
    from app.routes.api.interview_api import interview_api_bp
    from app.routes.api.analytics_api import analytics_api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(candidate_bp, url_prefix='/candidate')
    app.register_blueprint(recruiter_bp, url_prefix='/recruiter')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(job_bp)
    app.register_blueprint(auth_api_bp, url_prefix='/api')
    app.register_blueprint(job_api_bp, url_prefix='/api')
    app.register_blueprint(application_api_bp, url_prefix='/api')
    app.register_blueprint(interview_api_bp, url_prefix='/api')
    app.register_blueprint(analytics_api_bp, url_prefix='/api')

    @app.route('/')
    def index():
        return render_template('home.html')

    @app.route('/health')
    def health():
        database_connected = False
        if app.config.get('MONGO_AVAILABLE'):
            try:
                mongo.get_db().command('ping')
                database_connected = True
            except PyMongoError:
                database_connected = False
        return {
            'status': 'ok' if database_connected else 'unavailable',
            'database': app.config['MONGO_DB_NAME'],
            'mongodb_connected': database_connected,
        }, 200 if database_connected else 503

    @app.errorhandler(404)
    def not_found(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def server_error(error):
        return render_template('errors/500.html'), 500

    return app
