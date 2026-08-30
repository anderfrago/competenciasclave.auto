from pathlib import Path

from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
from flask import Flask, abort, jsonify, send_from_directory

from .config import Config
from .extensions import cors, db, jwt, migrate

oauth = OAuth()


def create_app() -> Flask:
    load_dotenv(Path(__file__).resolve().parents[2] / ".env")
    app = Flask(__name__, instance_relative_config=True)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    app.config.from_object(Config)
    app.config["SQLALCHEMY_DATABASE_URI"] = Config.database_uri(app.instance_path)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": [app.config["FRONTEND_URL"]]}}, supports_credentials=False)

    if app.config["GOOGLE_CLIENT_ID"] and app.config["GOOGLE_CLIENT_SECRET"]:
        oauth.init_app(app)
        oauth.register(
            name="google",
            client_id=app.config["GOOGLE_CLIENT_ID"],
            client_secret=app.config["GOOGLE_CLIENT_SECRET"],
            server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
            client_kwargs={"scope": "openid email profile"},
        )

    from .routes.admin import admin_bp
    from .routes.auth import auth_bp
    from .routes.public import public_bp
    from .routes.student import student_bp
    from .routes.tutor import tutor_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(public_bp, url_prefix="/api")
    app.register_blueprint(student_bp, url_prefix="/api/student")
    app.register_blueprint(tutor_bp, url_prefix="/api/tutor")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok"})

    spa_dist = Path(app.config["SPA_DIST_PATH"])
    if app.config["SPA_DIST_PATH"] and spa_dist.is_dir():
        @app.route("/", defaults={"path": ""})
        @app.route("/<path:path>")
        def single_page_app(path):
            if path.startswith("api/"):
                abort(404)
            requested = spa_dist / path
            if path and requested.is_file():
                return send_from_directory(spa_dist, path)
            return send_from_directory(spa_dist, "index.html")

    return app
