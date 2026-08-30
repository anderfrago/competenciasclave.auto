from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db


course_tutors = db.Table(
    "course_tutors",
    db.Column("course_id", db.Integer, db.ForeignKey("courses.id"), primary_key=True),
    db.Column("user_id", db.Integer, db.ForeignKey("users.id"), primary_key=True),
)


class TimestampMixin:
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class User(TimestampMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(160), nullable=False)
    password_hash = db.Column(db.String(255))
    role = db.Column(db.String(20), nullable=False, default="student")
    email_verified = db.Column(db.Boolean, nullable=False, default=False)
    auth_provider = db.Column(db.String(20), nullable=False, default="local")
    google_subject = db.Column(db.String(255), unique=True)
    enrollments = db.relationship("Enrollment", back_populates="student", cascade="all, delete-orphan")
    submissions = db.relationship("Submission", back_populates="student", cascade="all, delete-orphan")

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return bool(self.password_hash) and check_password_hash(self.password_hash, password)

    def as_dict(self) -> dict:
        return {
            "id": self.id,
            "email": self.email,
            "fullName": self.full_name,
            "role": self.role,
            "emailVerified": self.email_verified,
            "authProvider": self.auth_provider,
        }


class Course(TimestampMixin, db.Model):
    __tablename__ = "courses"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), nullable=False)
    academic_year = db.Column(db.String(20), nullable=False)
    active = db.Column(db.Boolean, nullable=False, default=True)
    invite_code = db.Column(db.String(40), unique=True, nullable=False, default=lambda: uuid4().hex)
    tutors = db.relationship("User", secondary=course_tutors, lazy="selectin")
    enrollments = db.relationship("Enrollment", back_populates="course", cascade="all, delete-orphan")
    submissions = db.relationship("Submission", back_populates="course", cascade="all, delete-orphan")

    def as_dict(self, include_code: bool = True) -> dict:
        data = {
            "id": self.id,
            "name": self.name,
            "academicYear": self.academic_year,
            "active": self.active,
            "tutors": [tutor.as_dict() for tutor in self.tutors],
        }
        if include_code:
            data["inviteCode"] = self.invite_code
        return data


class Enrollment(TimestampMixin, db.Model):
    __tablename__ = "enrollments"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)
    student = db.relationship("User", back_populates="enrollments")
    course = db.relationship("Course", back_populates="enrollments")
    __table_args__ = (db.UniqueConstraint("student_id", "course_id", name="uq_enrollment"),)


class Competency(TimestampMixin, db.Model):
    __tablename__ = "competencies"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), unique=True, nullable=False)
    description = db.Column(db.Text)
    sort_order = db.Column(db.Integer, nullable=False, default=0)
    active = db.Column(db.Boolean, nullable=False, default=True)
    items = db.relationship("CompetencyItem", back_populates="competency", cascade="all, delete-orphan", order_by="CompetencyItem.sort_order")
    rubric_levels = db.relationship("RubricLevel", back_populates="competency", cascade="all, delete-orphan", order_by="RubricLevel.max_score")

    def as_dict(self, with_items: bool = False) -> dict:
        data = {"id": self.id, "name": self.name, "description": self.description, "sortOrder": self.sort_order, "active": self.active,
                "rubricLevels": [level.as_dict() for level in self.rubric_levels]}
        if with_items:
            data["items"] = [item.as_dict() for item in self.items if item.active]
        return data


class CompetencyItem(TimestampMixin, db.Model):
    __tablename__ = "competency_items"
    id = db.Column(db.Integer, primary_key=True)
    competency_id = db.Column(db.Integer, db.ForeignKey("competencies.id"), nullable=False)
    statement = db.Column(db.Text, nullable=False)
    reverse_score = db.Column(db.Boolean, nullable=False, default=False)
    sort_order = db.Column(db.Integer, nullable=False, default=0)
    active = db.Column(db.Boolean, nullable=False, default=True)
    competency = db.relationship("Competency", back_populates="items")

    def as_dict(self) -> dict:
        return {"id": self.id, "competencyId": self.competency_id, "statement": self.statement,
                "reverseScore": self.reverse_score, "sortOrder": self.sort_order, "active": self.active}


class RubricLevel(TimestampMixin, db.Model):
    __tablename__ = "rubric_levels"
    id = db.Column(db.Integer, primary_key=True)
    competency_id = db.Column(db.Integer, db.ForeignKey("competencies.id"), nullable=False)
    label = db.Column(db.String(80), nullable=False)
    max_score = db.Column(db.Float, nullable=False)
    feedback = db.Column(db.Text, nullable=False)
    competency = db.relationship("Competency", back_populates="rubric_levels")
    __table_args__ = (db.UniqueConstraint("competency_id", "label", name="uq_competency_level"),)

    def as_dict(self) -> dict:
        return {"id": self.id, "label": self.label, "maxScore": self.max_score, "feedback": self.feedback}


class Submission(TimestampMixin, db.Model):
    __tablename__ = "submissions"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)
    completed_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    encouragement = db.Column(db.Text)
    student = db.relationship("User", back_populates="submissions")
    course = db.relationship("Course", back_populates="submissions")
    answers = db.relationship("Answer", back_populates="submission", cascade="all, delete-orphan")
    results = db.relationship("CompetencyResult", back_populates="submission", cascade="all, delete-orphan")

    def as_dict(self, include_answers: bool = False) -> dict:
        data = {"id": self.id, "student": self.student.as_dict(), "course": self.course.as_dict(False),
                "completedAt": self.completed_at.isoformat(), "encouragement": self.encouragement,
                "results": [result.as_dict() for result in sorted(self.results, key=lambda r: r.competency.sort_order)]}
        if include_answers:
            data["answers"] = [answer.as_dict() for answer in self.answers]
        return data


class Answer(db.Model):
    __tablename__ = "answers"
    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey("submissions.id"), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey("competency_items.id"), nullable=False)
    value = db.Column(db.Integer, nullable=False)
    submission = db.relationship("Submission", back_populates="answers")
    item = db.relationship("CompetencyItem")
    __table_args__ = (db.UniqueConstraint("submission_id", "item_id", name="uq_answer"),)

    def as_dict(self) -> dict:
        return {"itemId": self.item_id, "value": self.value}


class CompetencyResult(db.Model):
    __tablename__ = "competency_results"
    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey("submissions.id"), nullable=False)
    competency_id = db.Column(db.Integer, db.ForeignKey("competencies.id"), nullable=False)
    score = db.Column(db.Float, nullable=False)
    level = db.Column(db.String(80), nullable=False)
    feedback = db.Column(db.Text, nullable=False)
    submission = db.relationship("Submission", back_populates="results")
    competency = db.relationship("Competency")
    __table_args__ = (db.UniqueConstraint("submission_id", "competency_id", name="uq_result"),)

    def as_dict(self) -> dict:
        return {"competencyId": self.competency_id, "competency": self.competency.name, "score": round(self.score, 2),
                "level": self.level, "feedback": self.feedback}


class AppSetting(db.Model):
    __tablename__ = "app_settings"
    key = db.Column(db.String(100), primary_key=True)
    value = db.Column(db.Text, nullable=False)

