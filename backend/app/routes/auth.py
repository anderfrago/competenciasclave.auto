import smtplib

from flask import Blueprint, current_app, jsonify, redirect, request, url_for
from flask_jwt_extended import create_access_token, jwt_required, set_access_cookies, unset_jwt_cookies
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
    response = jsonify({"user": user.as_dict()})
    set_access_cookies(response, create_access_token(identity=str(user.id), additional_claims={"version": user.auth_version}))
    return response


@auth_bp.post("/register")
def register():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    full_name = (data.get("fullName") or "").strip()
    password = data.get("password") or ""
    if not email or not full_name or len(password) < 8:
        return jsonify({"error": "Indica nombre, correo y una contraseña de al menos 8 caracteres."}), 400
    if email not in current_app.config["REGISTRATION_EMAILS"]:
        return jsonify({"error": "Solicita al centro que autorice tu correo antes de registrarte."}), 403
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Ya existe una cuenta con este correo. Inicia sesión."}), 409

    user = User(email=email, full_name=full_name, auth_provider="local")
    user.set_password(password)
    sync_role(user)
    db.session.add(user)
    db.session.flush()
    verification_token = serializer().dumps({"id": user.id, "email": email, "version": user.auth_version})
    verification_url = f"{current_app.config['BACKEND_URL']}/api/auth/verify/{verification_token}"
    try:
        sent = send_email(email, "Verifica tu cuenta", f"Abre este enlace para verificar tu cuenta:\n{verification_url}")
    except (smtplib.SMTPException, OSError):
        sent = False
    if not sent:
        db.session.rollback()
        return jsonify({"error": "No se ha podido enviar la verificación. Contacta con el centro."}), 503
    db.session.commit()
    return jsonify({"message": "Te hemos enviado un enlace de verificación al correo indicado."}), 201


@auth_bp.get("/verify/<token>")
def verify_email(token):
    try:
        data = serializer().loads(token, max_age=60 * 60 * 24)
    except SignatureExpired:
        return jsonify({"error": "El enlace de verificación ha caducado."}), 400
    except BadSignature:
        return jsonify({"error": "El enlace de verificación no es válido."}), 400
    if not isinstance(data, dict):
        return jsonify(error="Enlace no válido."), 400
    user = db.session.get(User, data.get("id"))
    if not user or not user.active or user.email_verified or user.email != data.get("email") or user.auth_version != data.get("version"):
        return jsonify(error="Enlace no válido."), 400
    user.email_verified = True
    sync_role(user)
    db.session.commit()
    return redirect(f"{current_app.config['FRONTEND_URL']}/acceso?verified=1")


@auth_bp.post("/login")
def login():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    user = User.query.filter_by(email=email).first()
    if not user or not user.active or not user.check_password(data.get("password") or ""):
        return jsonify({"error": "Correo o contraseña incorrectos."}), 401
    if not user.email_verified:
        return jsonify({"error": "Debes verificar tu correo antes de iniciar sesión."}), 403
    return token_response(user)


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
    subject = info.get("sub")
    if not subject:
        return jsonify(error="Identidad no válida."), 400
    user = User.query.filter_by(email=email).first()
    linked = User.query.filter_by(google_subject=subject).first()
    if (linked and linked != user) or (user and user.google_subject and user.google_subject != subject):
        return jsonify(error="La identidad no coincide con la cuenta autorizada."), 403
    if not user:
        if email not in current_app.config["REGISTRATION_EMAILS"] and email not in current_app.config["ADMIN_EMAILS"]:
            return jsonify(error="Solicita al centro que autorice tu correo."), 403
        user = User(email=email, full_name=info.get("name") or email.split("@")[0], auth_provider="google", google_subject=subject, email_verified=True)
        db.session.add(user)
        db.session.flush()
    if not user.active:
        return jsonify(error="Cuenta desactivada."), 403
    if not user.email_verified:
        # A password chosen before proving ownership must not survive Google verification.
        user.password_hash = None
        user.auth_version += 1
    user.google_subject = subject
    user.auth_provider = "google"
    user.email_verified = True
    sync_role(user)
    db.session.commit()
    response = redirect(f"{current_app.config['FRONTEND_URL']}/acceso?google=1")
    set_access_cookies(response, create_access_token(identity=str(user.id), additional_claims={"version": user.auth_version}))
    return response


@auth_bp.post("/logout")
@jwt_required()
def logout():
    user = current_user()
    user.auth_version += 1
    db.session.commit()
    response = jsonify(message="Sesiones cerradas.")
    unset_jwt_cookies(response)
    return response


@auth_bp.get("/me")
@jwt_required()
def me():
    user = current_user()
    sync_role(user)
    db.session.commit()
    return jsonify({"user": user.as_dict()})

