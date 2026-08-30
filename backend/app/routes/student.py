from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from ..auth import current_user
from ..extensions import db
from ..models import Course, Enrollment, Submission
from ..services import submit_questionnaire

student_bp = Blueprint("student", __name__)


@student_bp.get("/courses")
@jwt_required()
def my_courses():
    user = current_user()
    return jsonify({"courses": [enrollment.course.as_dict(False) for enrollment in user.enrollments]})


@student_bp.post("/courses/<invite_code>/enroll")
@jwt_required()
def enroll(invite_code):
    user = current_user()
    if user.role not in ("student", "tutor", "admin"):
        return jsonify({"error": "No es posible inscribirse con esta cuenta."}), 403
    course = Course.query.filter_by(invite_code=invite_code, active=True).first_or_404()
    if not Enrollment.query.filter_by(student_id=user.id, course_id=course.id).first():
        db.session.add(Enrollment(student_id=user.id, course_id=course.id))
        db.session.commit()
    return jsonify({"course": course.as_dict(False)}), 201


@student_bp.post("/submissions")
@jwt_required()
def create_submission():
    user = current_user()
    data = request.get_json() or {}
    course_id = data.get("courseId")
    course = db.session.get(Course, course_id)
    if not course or not Enrollment.query.filter_by(student_id=user.id, course_id=course.id).first():
        return jsonify({"error": "No perteneces a este curso."}), 403
    try:
        answers = {int(answer["itemId"]): int(answer["value"]) for answer in data.get("answers", [])}
        submission = submit_questionnaire(user, course, answers)
    except (KeyError, TypeError, ValueError) as error:
        return jsonify({"error": str(error)}), 400
    return jsonify({"submission": submission.as_dict()}), 201


@student_bp.get("/submissions")
@jwt_required()
def list_submissions():
    user = current_user()
    course_id = request.args.get("courseId", type=int)
    query = Submission.query.filter_by(student_id=user.id)
    if course_id:
        query = query.filter_by(course_id=course_id)
    submissions = query.order_by(Submission.completed_at.desc()).all()
    return jsonify({"submissions": [submission.as_dict() for submission in submissions]})


@student_bp.get("/submissions/<int:submission_id>")
@jwt_required()
def get_submission(submission_id):
    user = current_user()
    submission = Submission.query.get_or_404(submission_id)
    if submission.student_id != user.id:
        return jsonify({"error": "No tienes acceso a este resultado."}), 403
    return jsonify({"submission": submission.as_dict(include_answers=True)})

