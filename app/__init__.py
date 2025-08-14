import os
from flask import Flask, render_template
from flask_login import current_user
from datetime import datetime
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
    # Default logging; debug can be enabled via FLASK_DEBUG env when needed

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
        from .models import persona  # registers CommStyle, Persona, PersonaStyle
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
    from .blueprints.styles.routes import styles_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(interview_bp, url_prefix="/interview")
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(styles_bp, url_prefix="/styles")

    # Root
    @app.get("/")
    def index():
        # Provide a lightweight dashboard when authenticated
        context = {}
        try:
            if current_user.is_authenticated:
                from .models.interview import Interview, Message
                from .models.summary import Summary
                from .models.persona import Persona

                interviews = (
                    Interview.query.filter_by(user_id=current_user.id)
                    .order_by(Interview.created_at.desc())
                    .all()
                )
                # Compute simple message counts per interview id
                msg_counts = {i.id: Message.query.filter_by(interview_id=i.id).count() for i in interviews}
                # Summary presence per interview id
                summary_ids = {s.interview_id for s in Summary.query.filter_by(user_id=current_user.id).all()}
                # Personas overview
                persona_count = Persona.query.filter_by(user_id=current_user.id).count()
                default_persona = (
                    Persona.query.filter_by(user_id=current_user.id, is_default=True).first()
                    or Persona.query.filter_by(is_system=True, is_default=True).first()
                )

                context.update(
                    total_interviews=len(interviews),
                    interviews=interviews[:5],  # show a few recent on the home page
                    msg_counts=msg_counts,
                    summary_ids=summary_ids,
                    persona_count=persona_count,
                    default_persona=default_persona,
                    summaries_count=Summary.query.filter_by(user_id=current_user.id).count(),
                )
        except Exception:
            # If any dashboard query fails, render the page without dashboard data
            context = {}
        # Always include current year for footer
        context.setdefault("current_year", datetime.utcnow().year)
        return render_template("index.html", **context)

    return app
