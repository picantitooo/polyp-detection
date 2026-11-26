<script lang="ts">
	import { resolve } from '$app/paths';
	import { useSessions } from '$lib/sessions/context.svelte';
	import colon from '$lib/assets/colon-detection.png';
	const sessions = useSessions();
	let { title, description, features }: { title: string; description: string; features: string[] } =
		$props();
</script>

<svelte:head><title>{title} · Polyp</title></svelte:head>
<div class="module-heading" class:report-heading={title === 'Informes'}>
	{#if title === 'Informes'}
		<svg class="report-wave" viewBox="0 0 1000 180" preserveAspectRatio="none" aria-hidden="true">
			<path d="M0 180C190 175 280 166 415 85S575 12 680 68 830 87 912 30 979 26 1000 38V180Z" />
		</svg>
	{/if}
	<span class="module-icon" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M6 3h8l4 4v14H6zM14 3v5h4m-9 5h6m-6 4h6" /></svg></span>
	<div><h1>{title}</h1><p>{description}</p></div>
	{#if title === 'Informes'}<img src={colon} alt="" class="module-art" />{/if}
</div>
{#if title === 'Informes'}
	<div class="metric-grid report-metrics">
		<section class="panel metric-card"><span class="metric-icon" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M5 3h14v18H5zM8 8h8m-8 4h8m-8 4h5" /></svg></span><div>Sesiones registradas<strong>{sessions.records.length}</strong></div></section>
		<section class="panel metric-card"><span class="metric-icon" aria-hidden="true"><svg viewBox="0 0 24 24"><circle cx="10" cy="10" r="6" /><path d="m15 15 6 6" /></svg></span><div>Hallazgos detectados<strong aria-label="Dato no disponible">—</strong></div></section>
		<section class="panel metric-card"><span class="metric-icon" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M4 20v-5h4v5zm6 0V9h4v11zm6 0V4h4v16z" /></svg></span><div>Informes generados<strong>0</strong></div></section>
	</div>
{/if}
<section class="clinical-module" class:report-module={title === 'Informes'}>
	<header><div><h2>{title} de la sesión</h2><p>Los elementos aparecerán aquí cuando una sesión envíe datos al servicio.</p></div><span class="badge">Sin registros</span></header>
	<div class="module-table-head"><span>Fecha y hora</span><span>Sesión</span><span>Estado</span><span>Detalle</span></div>
	<div class="module-empty">
		<svg viewBox="0 0 64 64" aria-hidden="true"><rect x="12" y="10" width="39" height="46" rx="6" /><path d="M23 10V6h17v9H23zM22 25h19M22 34h19M22 43h10" /><circle cx="49" cy="48" r="12" /><path d="M44 48h10m-5-5v10" /></svg>
		<h2>No hay información disponible</h2>
		<p>El registro de datos para este módulo aún está pendiente.</p>
		<a class="button primary" href={resolve('/sessions/new')}>+ Nueva sesión</a>
	</div>
	<footer><span>Las siguientes capacidades se conectarán con datos verificados.</span><ul>{#each features as feature (feature)}<li>{feature}</li>{/each}</ul></footer>
</section>
