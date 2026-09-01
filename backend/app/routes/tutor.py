from collections import defaultdict

from io import BytesIO

from flask import Blueprint, jsonify, send_file
from openpyxl import Workbook
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas

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


def _course_submissions(course_id):
    return Submission.query.filter_by(course_id=course_id).order_by(Submission.completed_at).all()


@tutor_bp.get("/courses/<int:course_id>/export.xlsx")
@roles_required("tutor", "admin")
def export_course_xlsx(course_id):
    user = current_user()
    course = Course.query.get_or_404(course_id)
    if not can_view_course(user, course):
        return jsonify({"error": "No tienes acceso a este curso."}), 403
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Resultados"
    submissions = _course_submissions(course.id)
    competencies = sorted({result.competency.name for item in submissions for result in item.results})
    sheet.append(["Alumno/a", "Correo", "Fecha", *competencies])
    for item in submissions:
        scores = {result.competency.name: result.score for result in item.results}
        sheet.append([item.student.full_name, item.student.email, item.completed_at.isoformat(),
                      *[round(scores.get(name), 2) if name in scores else "" for name in competencies]])
    sheet.freeze_panes = "A2"
    for column in sheet.columns:
        sheet.column_dimensions[column[0].column_letter].width = min(42, max(12, max(len(str(cell.value or "")) for cell in column) + 2))
    output = BytesIO()
    workbook.save(output)
    output.seek(0)
    return send_file(output, as_attachment=True, download_name=f"resultados-{course.id}.xlsx",
                     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@tutor_bp.get("/courses/<int:course_id>/export.pdf")
@roles_required("tutor", "admin")
def export_course_pdf(course_id):
    user = current_user()
    course = Course.query.get_or_404(course_id)
    if not can_view_course(user, course):
        return jsonify({"error": "No tienes acceso a este curso."}), 403
    output = BytesIO()
    pdf = canvas.Canvas(output, pagesize=landscape(A4))
    width, height = landscape(A4)
    y = height - 42
    pdf.setTitle(f"Resultados - {course.name}")
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(36, y, f"{course.name} · {course.academic_year}")
    y -= 28
    for item in _course_submissions(course.id):
        if y < 60:
            pdf.showPage(); y = height - 42
        pdf.setFont("Helvetica-Bold", 9)
        pdf.drawString(36, y, f"{item.student.full_name} · {item.completed_at.strftime('%d/%m/%Y %H:%M')}")
        y -= 14
        pdf.setFont("Helvetica", 8)
        text = " | ".join(f"{result.competency.name}: {result.score:.2f} ({result.level})" for result in item.results)
        for start in range(0, len(text), 150):
            pdf.drawString(48, y, text[start:start + 150]); y -= 11
        y -= 7
    pdf.save()
    output.seek(0)
    return send_file(output, as_attachment=True, download_name=f"resultados-{course.id}.pdf", mimetype="application/pdf")
