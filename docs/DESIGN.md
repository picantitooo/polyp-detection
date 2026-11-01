# Interfaz del puesto de endoscopia

## Criterio

Blanco para superficies de trabajo, celeste para selección y azul con contraste para la acción principal. El video ocupa el espacio dominante. No agregar adornos para llenar estados vacíos.

- Navegación con nombres, sin numeración, logotipo de letra ni etiquetas superiores decorativas.
- Mantener los módulos pendientes como pidió el usuario; indicar su estado dentro de la vista, no repetir pills por todo el menú.
- Inicio queda pendiente, sin dashboard ni módulos duplicados.
- Sesiones es una tabla con fecha, fuente, estado, duración y enlace Abrir. No hay tarjeta de relleno ni alertas grandes de almacenamiento.
- Única nota de retención junto al historial: las sesiones se borran al recargar.
- Advertencias y alcance clínico se explican en Ayuda; la navegación identifica la versión de investigación.
- Preparación: fuente y botones Previsualizar / Iniciar asistencia dentro del panel derecho. Cancelar en el mismo panel.
- Procedimiento: mostrar original/anotaciones, detener/reintentar y finalizar en el panel derecho. Finalizar se separa de las acciones frecuentes.
- Eliminar acciones deshabilitadas que no aportan información a la tarea. La sección Eventos informa que aún está pendiente.
- Sidebar estable y oculto durante el procedimiento. En móvil se abre mediante Menú.
- Video con object-fit:contain; el workspace usa el alto disponible. En pantallas bajas o estrechas se permite reflujo en lugar de recortar acciones.

## Referencias consultadas

- Anthropic frontend-design: https://github.com/anthropics/skills/blob/main/skills/frontend-design/SKILL.md
- NHS, jerarquía de botones: https://service-manual.nhs.uk/design-system/components/buttons

Se consultaron como referencias de diseño; no se instaló una habilidad externa ni se copió una interfaz clínica. No implican validación médica del producto.

## Aplicar esta actualización

Desde la raíz de polyp-detection, después de guardar los cambios locales:

```bash
unzip -o polyp-design-update.zip
cd frontend
npm run check
npm run dev -- --port 5173 --strictPort
```

El ZIP contiene solo los archivos modificados. No cambia backend, modelos, dependencias ni el contrato WebRTC.

## Verificación

Svelte/TypeScript: 0 errores y advertencias. Build y ESLint de la aplicación modificada: correctos. Diez rutas SSR verificadas. No se completó el chequeo visual: Chromium falla al arrancar en este entorno. El test de navegador se actualizó, pero no se declara ejecutado ni superado. Comprobar en equipo real: 1366x768 y 1280x600; foco de teclado; panel derecho sin solapamientos; fuente de cámara; transición a procedimiento; finalizar liberando los recursos.
