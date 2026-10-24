from functools import wraps

from flask import abort, jsonify, redirect, url_for
from flask_login import current_user


def role_required(*allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            if current_user.role not in allowed_roles:
                abort(403)
            return view_func(*args, **kwargs)
        return wrapped

    return decorator


def api_role_required(*allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify({'error': 'authentication required'}), 401
            if current_user.role not in allowed_roles:
                return jsonify({'error': 'forbidden'}), 403
            return view_func(*args, **kwargs)
        return wrapped

    return decorator
