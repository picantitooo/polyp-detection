<script lang="ts">
	import DisplayPreferences from '$lib/components/DisplayPreferences.svelte';
	import UserGuide from '$lib/components/UserGuide.svelte';
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
		}
	};
	let module = $derived(modules[data.section]);
</script>

<svelte:head
	><title
		>{data.section === 'help'
			? 'Ayuda'
			: data.section === 'settings'
				? 'Configuración'
				: (module?.title ?? 'Polyp')} · Polyp</title
	></svelte:head
>
{#if data.section === 'help'}
	<UserGuide />
{:else if data.section === 'settings'}
	<DisplayPreferences />
{:else if module}
	<Placeholder {...module} />
{/if}
