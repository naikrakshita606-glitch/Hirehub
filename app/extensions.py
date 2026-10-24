import logging

from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from pymongo import MongoClient

logger = logging.getLogger(__name__)

bcrypt = Bcrypt()
login_manager = LoginManager()


class MongoManager:
    def __init__(self):
        self.client = None
        self.db = None

    def init_app(self, app):
        uri = app.config.get('MONGO_URI', 'mongodb://localhost:27017/hirehub')
        db_name = app.config.get('MONGO_DB_NAME', 'hirehub')
        app.config['MONGO_AVAILABLE'] = False
        client = None
        try:
            client = MongoClient(uri, serverSelectionTimeoutMS=2000)
            client.admin.command('ping')
            self.client = client
            self.db = client[db_name]
            app.config['MONGO_AVAILABLE'] = True
        except Exception as exc:
            if client is not None:
                client.close()
            self.client = None
            self.db = None
            app.config['MONGO_AVAILABLE'] = False
            if app.config.get('MONGO_REQUIRED', True):
                logger.error(
                    "MongoDB database '%s' is required but connection failed (%s).",
                    db_name,
                    type(exc).__name__,
                )
                raise RuntimeError(
                    f"MongoDB database '{db_name}' is required but unavailable."
                ) from exc
            logger.warning(
                'MongoDB connection failed (%s); using in-memory storage.',
                type(exc).__name__,
            )

    def get_db(self):
        return self.db


mongo = MongoManager()
