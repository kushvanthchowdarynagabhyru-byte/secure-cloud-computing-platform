import os
from flask import Flask, render_template
from flask_login import LoginManager

from config import Config
from models import db, User


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    if not app.config.get("MASTER_KEY"):
        raise RuntimeError(
            "MASTER_KEY is not set. Copy .env.example to .env and set a generated "
            "Fernet key before running the app."
        )

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(os.path.join(os.path.dirname(__file__), "instance"), exist_ok=True)

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "error"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    from auth import auth_bp
    from files import files_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(files_bp)

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("error.html", code=403, message="Access forbidden."), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("error.html", code=404, message="Page not found."), 404

    @app.errorhandler(413)
    def too_large(e):
        return render_template("error.html", code=413, message="File is too large."), 413

    with app.app_context():
        db.create_all()

    return app


if __name__ == "__main__":
    app = create_app()
    # debug=True is for local development only - turn off in production
    app.run(debug=True, host="127.0.0.1", port=5000)
