from flask import Blueprint, jsonify, request
from ..auth import current_user, roles_required
from ..extensions import db
from ..models import AppSetting, Competency, CompetencyItem, Course, RubricLevel, User

admin_bp = Blueprint("admin", __name__)


def body():
    return request.get_json() or {}


@admin_bp.get("/courses")
@roles_required("admin")
def list_courses():
    courses = Course.query.order_by(Course.academic_year.desc(), Course.name).all()
    return jsonify({"courses": [course.as_dict() for course in courses]})


@admin_bp.post("/courses")
@roles_required("admin")
def create_course():
    data = body()
    if not data.get("name") or not data.get("academicYear"):
        return jsonify({"error": "El nombre y el curso académico son obligatorios."}), 400
    course = Course(name=data["name"].strip(), academic_year=data["academicYear"].strip(), active=bool(data.get("active", True)))
    db.session.add(course)
    db.session.commit()
    return jsonify({"course": course.as_dict()}), 201


@admin_bp.patch("/courses/<int:course_id>")
@roles_required("admin")
def update_course(course_id):
    course = Course.query.get_or_404(course_id)
    data = body()
    course.name = data.get("name", course.name).strip()
    course.academic_year = data.get("academicYear", course.academic_year).strip()
    if "active" in data:
        course.active = bool(data["active"])
    db.session.commit()
    return jsonify({"course": course.as_dict()})


@admin_bp.delete("/courses/<int:course_id>")
@roles_required("admin")
def delete_course(course_id):
    course = Course.query.get_or_404(course_id)
    db.session.delete(course)
    db.session.commit()
    return "", 204


@admin_bp.post("/courses/<int:course_id>/tutors")
@roles_required("admin")
def add_tutor(course_id):
    course = Course.query.get_or_404(course_id)
    user = db.session.get(User, body().get("userId"))
    if not user:
        return jsonify({"error": "No se ha encontrado la persona tutora."}), 404
    user.role = "tutor" if user.role != "admin" else "admin"
    if user not in course.tutors:
        course.tutors.append(user)
    db.session.commit()
    return jsonify({"course": course.as_dict()})


@admin_bp.delete("/courses/<int:course_id>/tutors/<int:user_id>")
@roles_required("admin")
def remove_tutor(course_id, user_id):
    course = Course.query.get_or_404(course_id)
    tutor = db.session.get(User, user_id)
    if tutor and tutor in course.tutors:
        course.tutors.remove(tutor)
        db.session.commit()
    return "", 204


@admin_bp.get("/users")
@roles_required("admin")
def list_users():
    query = request.args.get("query", "").strip().lower()
    users = User.query.order_by(User.full_name).all()
    if query:
        users = [user for user in users if query in user.email.lower() or query in user.full_name.lower()]
    return jsonify({"users": [user.as_dict() for user in users]})


@admin_bp.post("/users")
@roles_required("admin")
def create_user():
    data = body()
    email = (data.get("email") or "").strip().lower()
    full_name = (data.get("fullName") or "").strip()
    role = data.get("role", "student")
    if not email or not full_name or role not in ("student", "tutor", "admin"):
        return jsonify({"error": "Nombre, correo y rol válido son obligatorios."}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Ya existe una cuenta con este correo."}), 409
    user = User(email=email, full_name=full_name, role=role,
                email_verified=bool(data.get("emailVerified", False)), auth_provider="local")
    password = data.get("password") or ""
    if password:
        if len(password) < 8:
            return jsonify({"error": "La contraseña debe tener al menos 8 caracteres."}), 400
        user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return jsonify({"user": user.as_dict()}), 201


@admin_bp.patch("/users/<int:user_id>")
@roles_required("admin")
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    data = body()
    if "email" in data:
        email = (data["email"] or "").strip().lower()
        duplicate = User.query.filter(User.email == email, User.id != user.id).first()
        if not email or duplicate:
            return jsonify({"error": "El correo no es válido o ya está en uso."}), 409
        user.email = email
    if "fullName" in data:
        user.full_name = (data["fullName"] or "").strip()
    if "role" in data:
        if data["role"] not in ("student", "tutor", "admin"):
            return jsonify({"error": "Rol no válido."}), 400
        user.role = data["role"]
    if "emailVerified" in data:
        user.email_verified = bool(data["emailVerified"])
    if data.get("password"):
        if len(data["password"]) < 8:
            return jsonify({"error": "La contraseña debe tener al menos 8 caracteres."}), 400
        user.set_password(data["password"])
    if not user.full_name:
        return jsonify({"error": "El nombre es obligatorio."}), 400
    db.session.commit()
    return jsonify({"user": user.as_dict()})


@admin_bp.delete("/users/<int:user_id>")
@roles_required("admin")
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user().id:
        return jsonify({"error": "No puedes eliminar tu propia cuenta mientras la utilizas."}), 400
    for course in list(Course.query.all()):
        if user in course.tutors:
            course.tutors.remove(user)
    db.session.delete(user)
    db.session.commit()
    return "", 204


@admin_bp.get("/competencies")
@roles_required("admin")
def list_competencies():
    competencies = Competency.query.order_by(Competency.sort_order).all()
    return jsonify({"competencies": [competency.as_dict(with_items=True) for competency in competencies]})


@admin_bp.post("/competencies")
@roles_required("admin")
def create_competency():
    data = body()
    competency = Competency(name=data.get("name", "").strip(), description=data.get("description"), sort_order=int(data.get("sortOrder", 999)), active=True)
    if not competency.name:
        return jsonify({"error": "El nombre es obligatorio."}), 400
    db.session.add(competency)
    db.session.flush()
    for label, maximum in (("Incipiente", 2.0), ("En desarrollo", 3.0), ("Generado", 4.0)):
        db.session.add(RubricLevel(competency_id=competency.id, label=label, max_score=maximum, feedback=f"Resultado {label} en {competency.name}."))
    db.session.commit()
    return jsonify({"competency": competency.as_dict(with_items=True)}), 201


@admin_bp.patch("/competencies/<int:competency_id>")
@roles_required("admin")
def update_competency(competency_id):
    competency = Competency.query.get_or_404(competency_id)
    data = body()
    for field, key in (("name", "name"), ("description", "description"), ("sort_order", "sortOrder"), ("active", "active")):
        if key in data:
            setattr(competency, field, data[key])
    db.session.commit()
    return jsonify({"competency": competency.as_dict(with_items=True)})


@admin_bp.delete("/competencies/<int:competency_id>")
@roles_required("admin")
def delete_competency(competency_id):
    db.session.delete(Competency.query.get_or_404(competency_id))
    db.session.commit()
    return "", 204


@admin_bp.post("/competencies/<int:competency_id>/items")
@roles_required("admin")
def create_item(competency_id):
    Competency.query.get_or_404(competency_id)
    data = body()
    item = CompetencyItem(competency_id=competency_id, statement=data.get("statement", "").strip(), reverse_score=bool(data.get("reverseScore")), sort_order=int(data.get("sortOrder", 999)))
    if not item.statement:
        return jsonify({"error": "El enunciado es obligatorio."}), 400
    db.session.add(item)
    db.session.commit()
    return jsonify({"item": item.as_dict()}), 201


@admin_bp.patch("/items/<int:item_id>")
@roles_required("admin")
def update_item(item_id):
    item = CompetencyItem.query.get_or_404(item_id)
    data = body()
    for field, key in (("statement", "statement"), ("reverse_score", "reverseScore"), ("sort_order", "sortOrder"), ("active", "active")):
        if key in data:
            setattr(item, field, data[key])
    db.session.commit()
    return jsonify({"item": item.as_dict()})


@admin_bp.delete("/items/<int:item_id>")
@roles_required("admin")
def delete_item(item_id):
    db.session.delete(CompetencyItem.query.get_or_404(item_id))
    db.session.commit()
    return "", 204


@admin_bp.patch("/rubric-levels/<int:level_id>")
@roles_required("admin")
def update_rubric_level(level_id):
    level = RubricLevel.query.get_or_404(level_id)
    data = body()
    for field, key in (("label", "label"), ("max_score", "maxScore"), ("feedback", "feedback")):
        if key in data:
            setattr(level, field, data[key])
    db.session.commit()
    return jsonify({"level": level.as_dict()})


@admin_bp.get("/settings")
@roles_required("admin")
def get_settings():
    setting = db.session.get(AppSetting, "encouragement_message")
    return jsonify({"encouragementMessage": setting.value if setting else ""})


@admin_bp.patch("/settings")
@roles_required("admin")
def update_settings():
    data = body()
    setting = db.session.get(AppSetting, "encouragement_message")
    if not setting:
        setting = AppSetting(key="encouragement_message", value="")
        db.session.add(setting)
    setting.value = data.get("encouragementMessage", "").strip()
    db.session.commit()
    return jsonify({"encouragementMessage": setting.value})
