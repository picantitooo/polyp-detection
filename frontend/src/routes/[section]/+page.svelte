<script lang="ts">
	import { resolve } from '$app/paths';
	import Placeholder from '$lib/components/Placeholder.svelte';
	let { data } = $props();
	const modules: Record<string, { title: string; description: string; features: string[] }> = {
		findings: {
			title: 'Hallazgos',
			description: 'Observaciones revisadas y vinculadas al procedimiento.',
			features: [
				'Revisar eventos de detección.',
				'Relacionar eventos con una misma lesión.',
				'Registrar localización, tamaño estimado y observaciones.'
			]
		},
		evidence: {
			title: 'Evidencia',
			description: 'Material visual asociado a las sesiones.',
			features: [
				'Capturas con referencia temporal.',
				'Clips seleccionados de eventos.',
				'Grabaciones con anotaciones sincronizadas.'
			]
		},
		reports: {
			title: 'Informes',
			description: 'Resúmenes de asistencia revisados por el médico.',
			features: [
				'Preparar un borrador de resumen.',
				'Revisar hallazgos y evidencia seleccionada.',
				'Exportar resultados.'
			]
		},
		models: {
			title: 'Modelos de IA',
			description: 'Información y trazabilidad de los componentes de inferencia.',
			features: [
				'Consultar la versión del detector.',
				'Consultar la versión del clasificador hiperplásico / adenoma.',
				'Mostrar compatibilidad y uso previsto. No permite cambiar pesos todavía.'
			]
		},
		settings: {
			title: 'Configuración',
			description: 'Preferencias del aplicativo.',
			features: [
				'Preferencias de visualización.',
				'Configuración de conservación de evidencia.',
				'La fuente de video se selecciona en cada sesión.'
			]
		}
	};
	let module = $derived(modules[data.section]);
</script>

<svelte:head
	><title>{data.section === 'help' ? 'Ayuda' : (module?.title ?? 'Polyp')} · Polyp</title
	></svelte:head
>
{#if data.section === 'help'}
	<div class="page-heading">
		<div>
			<h1>Ayuda</h1>
			<p class="muted">Recorrido y alcance de esta versión.</p>
		</div>
	</div>
	<section class="panel">
		<h2>Iniciar una sesión</h2>
		<ol class="help-steps">
			<li>Abre Nueva sesión y selecciona cámara/capturadora o un archivo de prueba autorizado.</li>
			<li>Solicita la previsualización y concede acceso al dispositivo.</li>
			<li>Inicia la asistencia. FastAPI debe estar disponible en la URL configurada.</li>
			<li>Alterna la vista entre la fuente original y el video anotado por el backend.</li>
			<li>Finaliza para consultar tiempos y estado del procedimiento.</li>
		</ol>
		<p class="notice">
			Los videos se transmiten para inferencia, pero esta versión no los graba. Los metadatos de
			sesión solo viven en memoria de la pestaña.
		</p>
		<h2>Limitaciones</h2>
		<p>
			El porcentaje representa el score del clasificador, no una probabilidad clínica calibrada. No
			existe seguimiento anatómico ni conteo de pólipos únicos. Eventos, clips, informes y
			persistencia están pendientes.
		</p>
		<p>
			La captura de pantalla/video requiere localhost o un contexto seguro compatible. En archivo de
			prueba se conserva la reproducción en bucle de la versión original.
		</p>
		<a href={resolve('/sessions/new')} class="button primary">Preparar sesión</a>
	</section>
{:else if module}<Placeholder {...module} />{/if}
