from __future__ import annotations

from functools import wraps

from flask import abort
from flask_login import current_user
from flask_login.utils import login_required as login_required

from .models import Permission


def permission_required(permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.can(permission):
                abort(403)
            return f(*args, **kwargs)

        return decorated_function

    return decorator


def mod_required(f):
    return permission_required(Permission.MODERATE)(f)


def admin_required(f):
    return permission_required(Permission.ADMIN)(f)
