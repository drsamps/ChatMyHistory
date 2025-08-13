import os
from flask import Flask, render_template
from dotenv import load_dotenv

from .extensions import db, bcrypt, login_manager


def create_app() -> Flask:
    # Load .env from project root explicitly and override existing env vars
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    env_path = os.path.join(project_root, ".env")
    load_dotenv(dotenv_path=env_path, override=True)

    # Import Config only after env has been loaded
    from .config import Config

    # Serve static from project-level ./static (aligns with Tailwind build path)
    app = Flask(__name__, static_folder="../static", template_folder="templates")
    app.config.from_object(Config())

    # Ensure storage directories exist
    os.makedirs(app.config["UPLOAD_DIR"], exist_ok=True)
    os.makedirs(app.config["MEDIA_DIR"], exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    # Create tables if not exist (for initial bootstrapping)
    with app.app_context():
        from .models import user, interview, media, prompt, summary  # noqa: F401
        from .models.user import User
        db.create_all()

        # Seed initial admin if none exists
        if User.query.count() == 0:
            admin_email = os.getenv("ADMIN_EMAIL")
            admin_password = os.getenv("ADMIN_PASSWORD")
            admin_name = os.getenv("ADMIN_NAME", "Administrator")
            if admin_email and admin_password:
                admin_user = User(name=admin_name, email=admin_email, is_admin=True)
                admin_user.set_password(admin_password)
                db.session.add(admin_user)
                db.session.commit()

    # Register blueprints
    from .blueprints.auth.routes import auth_bp
    from .blueprints.admin.routes import admin_bp
    from .blueprints.interview.routes import interview_bp
    from .blueprints.api.routes import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(interview_bp, url_prefix="/interview")
    app.register_blueprint(api_bp, url_prefix="/api")

    # Root
    @app.get("/")
    def index():
        return render_template("index.html")

    return app
