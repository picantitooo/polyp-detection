# Ajustes de interfaz

Este ZIP se aplica desde la raíz de polyp-detection y contiene solo cambios de frontend.

- Blanco y celeste, con controles azules de contraste mayor.
- Inicio mínimo: contenido pendiente, sin tarjetas que repitan el sidebar.
- Textos reducidos en placeholders y cabecera.
- App shell de altura 100dvh; solo main tiene overflow-y:auto.
- Sidebar estable, compacto en pantallas bajas; en pantallas estrechas se organiza como navegación superior.
- Se oculta durante la sesión en vivo, como antes.
- Al navegar se restablece el scroll del contenido.
- No cambia la lógica de inferencia, contratos de API ni dependencias.

Aplicar desde la raíz (guarda antes tus cambios):

unzip -o polyp-ui-update.zip
cd frontend
npm run check
npm run dev -- --port 5173 --strictPort

Validado: Svelte/TypeScript y build. ESLint de componentes modificados. Falta comprobación visual en navegador; Chromium no está disponible en este entorno. Probar al menos 1366x768, 1280x600 y pantalla estrecha: el contenido se desplaza, la navegación permanece y la vista de procedimiento oculta el sidebar.
