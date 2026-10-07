# Autopercepción de Competencias Clave

Aplicación para que el alumnado valore sus competencias clave, reciba una devolución y permita al profesorado tutor analizar la evolución de sus cursos.

El proyecto se divide en `backend` (Flask y SQLite) y `frontend` (Angular 21, Signals, Bootstrap y Sass). Consulta primero [Privacidad y actualización](docs/PRIVACIDAD_Y_ACTUALIZACION.md), que incluye el diagrama, las variables necesarias y la migración para PythonAnywhere. Esta guía actualiza las instrucciones de despliegue anteriores.

## Inicio rápido

1. Copia `.env.example` como `.env`, genera claves aleatorias y configura correos autorizados, SMTP y privacidad. Solo para desarrollo HTTP, usa `COOKIE_SECURE=false`.
2. Activa un entorno virtual e instala `backend/requirements.txt`. Desde `backend`, para una base nueva ejecuta `flask --app run db upgrade` y después `flask --app run init-db`. La carga inicial requiere la plantilla de cuestionario indicada en la guía, ausente del repositorio. Para bases existentes, sigue la migración documentada.
3. En `frontend`, instala las dependencias con `pnpm install --frozen-lockfile` y arranca `pnpm start`.
4. Ejecuta las pruebas desde `backend` con `python -m unittest discover -s tests -v`. Usan datos sintéticos y no requieren la plantilla.
