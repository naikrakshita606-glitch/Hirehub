from app import create_app

app = create_app()

with app.app_context():
    from app.services.auth_service import AuthService
    auth_service = AuthService()
    auth_service.seed_admin(
        email=app.config['DEFAULT_ADMIN_EMAIL'],
        password=app.config['DEFAULT_ADMIN_PASSWORD'],
    )
    print(f"Seeded admin user: {app.config['DEFAULT_ADMIN_EMAIL']}")
