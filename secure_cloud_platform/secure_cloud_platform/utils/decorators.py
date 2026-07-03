from functools import wraps
from flask import abort
from flask_login import current_user


def admin_required(view_func):
    """Restrict a route to users with the 'admin' role."""
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            abort(403)
        return view_func(*args, **kwargs)
    return wrapped
