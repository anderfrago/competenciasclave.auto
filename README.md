# Autopercepción de Competencias Clave

Aplicación para que el alumnado valore sus competencias clave, reciba una devolución y permita al profesorado tutor analizar la evolución de sus cursos.

El proyecto se divide en `backend` (Flask y SQLite) y `frontend` (Angular 21, Signals, Bootstrap y Sass). Consulta la guía de despliegue incluida en `docs/` para instalarlo en local y publicarlo en PythonAnywhere.

## Inicio rápido

1. Copia `.env.example` como `.env` y completa las claves necesarias.
2. Crea un entorno virtual en `backend`, instala `requirements.txt` y ejecuta `flask --app run.py init-db`.
3. En `frontend`, instala las dependencias con `pnpm install` y arranca `pnpm start`.
