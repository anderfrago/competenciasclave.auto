from app import create_app
from app.extensions import db
from app.seed_data import seed_database

app = create_app()


@app.cli.command("init-db")
def init_db():
    """Crea las tablas y carga el cuestionario inicial."""
    db.create_all()
    seed_database()
    print("Base de datos inicializada.")


if __name__ == "__main__":
    app.run(debug=True)

