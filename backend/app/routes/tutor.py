from collections import defaultdict

from flask import Blueprint, jsonify

from ..auth import current_user, roles_required
from ..models import Course, Submission

tutor_bp = Blueprint("tutor", __name__)


def can_view_course(user, course) -> bool:
    return user.role == "admin" or any(tutor.id == user.id for tutor in course.tutors)


@tutor_bp.get("/courses")
@roles_required("tutor", "admin")
def tutor_courses():
    user = current_user()
    courses = Course.query.order_by(Course.academic_year.desc(), Course.name).all() if user.role == "admin" else [
        course for course in Course.query.order_by(Course.academic_year.desc(), Course.name).all() if can_view_course(user, course)
    ]
    return jsonify({"courses": [course.as_dict() for course in courses]})


@tutor_bp.get("/courses/<int:course_id>/dashboard")
@roles_required("tutor", "admin")
def course_dashboard(course_id):
    user = current_user()
    course = Course.query.get_or_404(course_id)
    if not can_view_course(user, course):
        return jsonify({"error": "No tienes acceso a este curso."}), 403

    submissions = Submission.query.filter_by(course_id=course.id).order_by(Submission.completed_at.desc()).all()
    latest_by_student = {}
    for submission in submissions:
        latest_by_student.setdefault(submission.student_id, submission)
    latest = list(latest_by_student.values())

    competency_scores = defaultdict(list)
    level_counts = defaultdict(lambda: defaultdict(int))
    students = []
    for submission in latest:
        result_map = {result.competency.name: result for result in submission.results}
        for result in submission.results:
            competency_scores[result.competency.name].append(result.score)
            level_counts[result.competency.name][result.level] += 1
        students.append({
            "student": submission.student.as_dict(),
            "submissionId": submission.id,
            "completedAt": submission.completed_at.isoformat(),
            "scores": {name: round(result.score, 2) for name, result in result_map.items()},
            "levels": {name: result.level for name, result in result_map.items()},
        })

    trend = defaultdict(lambda: defaultdict(list))
    for submission in submissions:
        month = submission.completed_at.strftime("%Y-%m")
        for result in submission.results:
            trend[month][result.competency.name].append(result.score)

    return jsonify({
        "course": course.as_dict(),
        "summary": {"enrolledStudents": len(course.enrollments), "studentsWithResults": len(latest), "totalSubmissions": len(submissions)},
        "averages": [{"competency": name, "score": round(sum(scores) / len(scores), 2)} for name, scores in competency_scores.items()],
        "levels": [{"competency": name, "counts": counts} for name, counts in level_counts.items()],
        "students": sorted(students, key=lambda row: row["student"]["fullName"].lower()),
        "trend": [{"month": month, "scores": {name: round(sum(scores) / len(scores), 2) for name, scores in values.items()}} for month, values in sorted(trend.items())],
    })


@tutor_bp.get("/submissions/<int:submission_id>")
@roles_required("tutor", "admin")
def view_submission(submission_id):
    user = current_user()
    submission = Submission.query.get_or_404(submission_id)
    if not can_view_course(user, submission.course):
        return jsonify({"error": "No tienes acceso a este resultado."}), 403
    return jsonify({"submission": submission.as_dict(include_answers=True)})

