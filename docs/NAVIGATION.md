# Navegación para el médico

- Identificación: Polyp (nombre de trabajo), con el descriptor Asistencia en colonoscopia.
- Desktop: contraer el sidebar a una franja con un botón accesible para mostrarlo de nuevo. El estado se mantiene al navegar dentro de la pestaña, no tras recargar.
- Móvil: se mantiene el botón Menú; la navegación cierra tras seleccionar una página.
- Durante la asistencia se oculta todo el sidebar, como antes.
- Modelos no aparece como tarea clínica del menú principal. Se conserva la página técnica en Configuración → Detector y clasificador; no habilita cambios de modelo.
- Sesiones, Hallazgos, Evidencia e Informes permanecen como tareas principales. Los módulos pendientes siguen indicándolo en sus propias vistas.

Aplicar desde la raíz de polyp-detection:

unzip -o polyp-navigation-update.zip
cd frontend
npm run check
npm run dev -- --port 5173 --strictPort

Tipos, build y lint comprobados. La prueba de navegador está actualizada, pero no se ejecutó: Chromium no arranca en este entorno. Verificar que el botón contrae/expande, el contenido gana ancho, la navegación móvil funciona y el sidebar se oculta en la sesión.
