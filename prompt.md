<tech_stack>
Quiero desarrollar una aplicación web: backend con Flask y frontend con Angular 21 (usando signals, también en los servicios, los estilos con Bootstrap y Sass), base de datos SQLite.
</tech_stack>
<target>
La aplicación es un formularo de autopercepcción de competencias clave para el alumnado.
Un alumno se registra, selecciona curso y completa el formulario. Recive una nota numérica y un resuptado de rubríca por cada competencia clave (CC)
Cada curso tiene asignado un tutor(cuenta de corrego @cuatrovientos.org). El tutor analiza mediante graficos y tabla los valores de su curso.
El administrador (ander_frago@cuatrovientos.org) gestiona todos los elementos
<target>
Ahora mismo tengo un formulario de google que genera este archivo excel al descargar las respuesta: [Template Formulario CCs (respuestas).xlsx](<Template Formulario CCs (respuestas).xlsx>)&#x20;

<template_form>
En la pestaña Perfiles\_CC se pueden apreciar los items a valorar:

Las Competencias Clave (CC) son:
- Autonomía
- Adaptción al entorno
- Competencia digital
- Comunicación&#x20;
- Emprendimiento/Innovación
- Responsabilidad
- Trabajo en equipo

Los niveles son los resultados de la escala de la rubríca generada:
- Incipiente
- En Desarrollo
- Generado

Al completar el formulario el alumno selecciona entre:
- Nunca
- A veces
- En la mayoría de las veces
- Siempre
</template_form>


<casos_de_uso>
(1) El usuario debe registrarse mediante correo o cuenta de google valida (tambien las cuentas de educación.navarra.es que son de google).

(2) El tutor de curso son cuentas de Google de dominio cuatrovientos.org).

(3) Existen cursos y dentro de cursos un tutor y multiples alumnos. 
- El alumno rellena un formulario. El resultado es un valor numérico por cada competencia clave y una frase de explicaciór por cada competencia clave además de una frase final de ánimo
- El tutor revisa el curso, y analiza las respuestas de los alumnos, de manera grupal e individual.

(4) El administrador (cuentas de correo editable desde .env, incialmente ander_frago@cuatrovientos.org y fernando_olcoz@cuatrovientos.org) es capaz de gestionar los CRUD:
- CRUD de cursos 
- CRUD de tutores dentro de un curso
- CRUD de competencias clave
- CRUD de items por competencia clave

</casos_de_uso>

Preguntame todas las dudas que tengas.
Quiero hacer un despliegue en python anywhere desde Github
