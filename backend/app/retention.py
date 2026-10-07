from datetime import datetime, timedelta

import click

from .extensions import db
from .models import Course


def register_retention(app):
    @app.cli.command("purge-expired")
    @click.option("--course-id", multiple=True, type=int, help="Curso revisado; repetible.")
    @click.option("--execute", is_flag=True, help="Borrar los cursos seleccionados y sus datos asociados.")
    def purge_expired(course_id, execute):
        """Vista previa por defecto. El plazo empieza tras la última actividad o cierre."""
        try:
            days = int(app.config["RETENTION_DAYS"])
            if days <= 0:
                raise ValueError
        except (ValueError, TypeError):
            raise click.ClickException("Define RETENTION_DAYS como entero positivo aprobado por el centro.")
        cutoff = datetime.utcnow() - timedelta(days=days)
        eligible = []
        for course in Course.query.filter_by(active=False).all():
            dates = [course.updated_at, course.created_at]
            dates.extend(e.updated_at for e in course.enrollments)
            dates.extend(s.updated_at for s in course.submissions)
            dates.extend(s.completed_at for s in course.submissions)
            if max(dates) < cutoff:
                eligible.append(course)
        selected = set(course_id)
        if selected - {course.id for course in eligible}:
            raise click.ClickException("Hay cursos seleccionados que no cumplen el plazo o no están cerrados. No se ha borrado nada.")
        if execute and not selected:
            raise click.ClickException("Indica cada --course-id revisado antes de ejecutar.")
        targets = [course for course in eligible if not selected or course.id in selected]
        for course in targets:
            click.echo(f"Curso {course.id}: {len(course.submissions)} cuestionarios, {len(course.enrollments)} matrículas")
            if execute:
                db.session.delete(course)
        if execute:
            db.session.commit()
        click.echo(f"{'Borrados' if execute else 'Vista previa, sin borrado'}: {len(targets)} cursos. Las cuentas se conservan.")
