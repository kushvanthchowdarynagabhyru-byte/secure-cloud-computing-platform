"""
Promote an existing user to the 'admin' role.
Usage: python make_admin.py <username>
"""
import sys
from app import create_app
from models import db, User

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python make_admin.py <username>")
        sys.exit(1)

    username = sys.argv[1]
    app = create_app()

    with app.app_context():
        user = User.query.filter_by(username=username).first()
        if not user:
            print(f"No user found with username '{username}'.")
            sys.exit(1)
        user.role = "admin"
        db.session.commit()
        print(f"'{username}' is now an admin.")
