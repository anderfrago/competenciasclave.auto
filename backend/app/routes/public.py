from flask import Blueprint, jsonify

from ..models import Competency, Course

public_bp = Blueprint("public", __name__)


@public_bp.get("/questionnaire")
def questionnaire():
    competencies = Competency.query.filter_by(active=True).order_by(Competency.sort_order).all()
    return jsonify({"competencies": [competency.as_dict(with_items=True) for competency in competencies]})


@public_bp.get("/invitations/<invite_code>")
def invitation(invite_code):
    course = Course.query.filter_by(invite_code=invite_code, active=True).first_or_404()
    return jsonify({"course": course.as_dict(include_code=False)})

