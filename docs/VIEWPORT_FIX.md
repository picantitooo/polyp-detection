# Preparación y procedimiento ajustados al viewport

Aplicar desde la raíz de polyp-detection, encima de la actualización blanco/celeste:

unzip -o polyp-viewport-fix.zip
cd frontend
npm run check
npm run dev -- --port 5173 --strictPort

Cambios:
- Preparación y procedimiento son workspaces de altura disponible.
- Video flexible en altura, object-fit:contain, sin recorte ni deformación.
- Controles agrupados fuera del video, al pie del workspace.
- Iniciar, preparar, detener y finalizar no dependen del alto del video.
- Header compacto y sin footer duplicado en estas dos vistas.
- Se mantienen los elementos de video montados y la lógica WebRTC.
- Rutas de listado, detalle y ayuda conservan scroll.
- En ancho <=820px o alto <600px se permite reflujo con controles inferiores sticky para preservar acceso. No se ocultan acciones para forzar un encaje artificial.

Verificación: tipos sin errores/advertencias, build y ESLint correctos. No se completó verificación visual automatizada porque Chromium no está disponible. Probar con tu resolución y zoom (por ejemplo 1366x768 y 1280x600). No se modificó backend ni inferencia.
