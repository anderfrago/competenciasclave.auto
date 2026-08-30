from urllib.parse import quote

from flask import Blueprint, current_app, jsonify, redirect, request, url_for
from flask_jwt_extended import create_access_token, jwt_required
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from .. import oauth
from ..auth import current_user
from ..extensions import db
from ..models import User
from ..services import send_email, sync_role

auth_bp = Blueprint("auth", __name__)


def serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt="email-verification")


def token_response(user):
    sync_role(user)
    db.session.commit()
    return {"accessToken": create_access_token(identity=str(user.id)), "user": user.as_dict()}


@auth_bp.post("/register")
def register():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    full_name = (data.get("fullName") or "").strip()
    password = data.get("password") or ""
    if not email or not full_name or len(password) < 8:
        return jsonify({"error": "Indica nombre, correo y una contraseña de al menos 8 caracteres."}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Ya existe una cuenta con este correo. Inicia sesión."}), 409

    user = User(email=email, full_name=full_name, auth_provider="local")
    user.set_password(password)
    sync_role(user)
    db.session.add(user)
    db.session.commit()
    verification_token = serializer().dumps(email)
    verification_url = f"{current_app.config['BACKEND_URL']}/api/auth/verify/{verification_token}"
    sent = send_email(email, "Verifica tu cuenta", f"Abre este enlace para verificar tu cuenta:\n{verification_url}")
    response = {"message": "Te hemos enviado un enlace de verificación al correo indicado."}
    if current_app.debug and not sent:
        response["verificationUrl"] = verification_url
    return jsonify(response), 201


@auth_bp.get("/verify/<token>")
def verify_email(token):
    try:
        email = serializer().loads(token, max_age=60 * 60 * 24)
    except SignatureExpired:
        return jsonify({"error": "El enlace de verificación ha caducado."}), 400
    except BadSignature:
        return jsonify({"error": "El enlace de verificación no es válido."}), 400
    user = User.query.filter_by(email=email).first_or_404()
    user.email_verified = True
    sync_role(user)
    db.session.commit()
    return redirect(f"{current_app.config['FRONTEND_URL']}/acceso?verified=1")


@auth_bp.post("/login")
def login():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(data.get("password") or ""):
        return jsonify({"error": "Correo o contraseña incorrectos."}), 401
    if not user.email_verified:
        return jsonify({"error": "Debes verificar tu correo antes de iniciar sesión."}), 403
    return jsonify(token_response(user))


@auth_bp.get("/google")
def google_login():
    if not current_app.config["GOOGLE_CLIENT_ID"]:
        return jsonify({"error": "El acceso con Google aún no está configurado."}), 503
    return oauth.google.authorize_redirect(url_for("auth.google_callback", _external=True))


@auth_bp.get("/google/callback")
def google_callback():
    token = oauth.google.authorize_access_token()
    info = token.get("userinfo") or oauth.google.parse_id_token(token)
    email = (info.get("email") or "").lower()
    if not email or not info.get("email_verified"):
        return jsonify({"error": "Google no ha confirmado la dirección de correo."}), 400
    user = User.query.filter((User.google_subject == info["sub"]) | (User.email == email)).first()
    if not user:
        user = User(email=email, full_name=info.get("name") or email.split("@")[0], auth_provider="google", google_subject=info["sub"], email_verified=True)
        db.session.add(user)
    else:
        user.google_subject = info["sub"]
        user.auth_provider = "google"
        user.email_verified = True
    payload = token_response(user)
    return redirect(f"{current_app.config['FRONTEND_URL']}/acceso?token={quote(payload['accessToken'])}")


@auth_bp.get("/me")
@jwt_required()
def me():
    user = current_user()
    sync_role(user)
    db.session.commit()
    return jsonify({"user": user.as_dict()})

