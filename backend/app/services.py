from __future__ import annotations

import smtplib
from email.message import EmailMessage
from statistics import mean

from flask import current_app

from .extensions import db
from .models import AppSetting, Competency, CompetencyResult, Submission


def sync_role(user) -> None:
    if user.email.lower() in current_app.config["ADMIN_EMAILS"]:
        user.role = "admin"


def send_email(recipient: str, subject: str, body: str) -> bool:
    """Envía correo SMTP; en local sin SMTP deja el enlace visible en el registro."""
    config = current_app.config
    if not config["SMTP_HOST"] or not config["SMTP_USERNAME"] or not config["SMTP_PASSWORD"]:
        current_app.logger.warning("SMTP sin configurar. Correo para %s: %s", recipient, body)
        return False
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = config["SMTP_FROM"]
    message["To"] = recipient
    message.set_content(body)
    with smtplib.SMTP(config["SMTP_HOST"], config["SMTP_PORT"]) as server:
        server.starttls()
        server.login(config["SMTP_USERNAME"], config["SMTP_PASSWORD"])
        server.send_message(message)
    return True


def submit_questionnaire(student, course, answers: dict[int, int]) -> Submission:
    competencies = Competency.query.filter_by(active=True).order_by(Competency.sort_order).all()
    expected_ids = {item.id for competency in competencies for item in competency.items if item.active}
    if expected_ids != set(answers):
        missing = expected_ids - set(answers)
        extra = set(answers) - expected_ids
        raise ValueError(f"El cuestionario no está completo. Faltan: {len(missing)}. No válidas: {len(extra)}.")
    if any(value not in (1, 2, 3, 4) for value in answers.values()):
        raise ValueError("Todas las respuestas deben tener un valor entre 1 y 4.")

    encouragement = db.session.get(AppSetting, "encouragement_message")
    submission = Submission(student=student, course=course, encouragement=encouragement.value if encouragement else None)
    db.session.add(submission)
    db.session.flush()

    from .models import Answer

    for competency in competencies:
        values = []
        for item in competency.items:
            if not item.active:
                continue
            raw_value = answers[item.id]
            scored_value = 5 - raw_value if item.reverse_score else raw_value
            values.append(scored_value)
            db.session.add(Answer(submission_id=submission.id, item_id=item.id, value=raw_value))

        score = mean(values)
        rubric = next((level for level in competency.rubric_levels if score <= level.max_score), competency.rubric_levels[-1])
        db.session.add(
            CompetencyResult(
                submission_id=submission.id,
                competency_id=competency.id,
                score=score,
                level=rubric.label,
                feedback=rubric.feedback,
            )
        )

    db.session.commit()
    return submission
