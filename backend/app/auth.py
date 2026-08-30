from functools import wraps

from flask import jsonify
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

from .extensions import db
from .models import User


def current_user():
    identity = get_jwt_identity()
    return db.session.get(User, int(identity)) if identity else None


def roles_required(*roles):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            verify_jwt_in_request()
            user = current_user()
            if not user or user.role not in roles:
                return jsonify({"error": "No tienes permiso para realizar esta acción."}), 403
            return view(*args, **kwargs)
        return wrapped
    return decorator
