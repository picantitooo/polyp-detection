<script lang="ts">
	import DisplayPreferences from '$lib/components/DisplayPreferences.svelte';
	import UserGuide from '$lib/components/UserGuide.svelte';
	import StationSettings from '$lib/components/StationSettings.svelte';
	import { page } from '$app/state';
	import EvidenceRecords from '$lib/components/EvidenceRecords.svelte';
	import EvidenceIndex from '$lib/components/EvidenceIndex.svelte';
	import SessionReports from '$lib/components/SessionReports.svelte';
	import { resolve } from '$app/paths';
	let { data } = $props();
 const titles: Record<string,string> = { findings:'Hallazgos', evidence:'Evidencia', reports:'Informes', models:'Modelos de IA', settings:'Configuración', accessibility:'Accesibilidad', help:'Ayuda' };
</script>

<svelte:head><title>{titles[data.section]} · EndoSight</title></svelte:head>
{#if data.section === 'help'}
	<UserGuide />
{:else if data.section === 'settings'}
	<StationSettings />
{:else if data.section === 'accessibility'}
	<DisplayPreferences />
{:else if page.params.section === 'reports'}
	<SessionReports />
{:else if page.params.section === 'evidence'}
	<EvidenceIndex />
{:else if page.params.section === 'findings'}
	<EvidenceRecords mode="findings" />
{:else}
	<section class="support-page"><header><h1>Modelos de IA</h1><p class="muted">Componentes de la asistencia experimental.</p></header><div class="panel"><h2>Detección y clasificación</h2><p>El detector señala regiones del video. El clasificador propone las etiquetas hiperplásico o adenoma para revisión del especialista.</p><dl class="settings-metadata"><dt>Versión del detector</dt><dd>Información no disponible</dd><dt>Versión del clasificador</dt><dd>Información no disponible</dd></dl></div><a href={resolve('/settings')}>Volver a Configuración</a></section>
{/if}
