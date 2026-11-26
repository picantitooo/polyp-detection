<script lang="ts">
	import { resolve } from '$app/paths';
	import EvidenceRecords from '$lib/components/EvidenceRecords.svelte';
	import colon from '$lib/assets/colon-detection.png';
	import { page } from '$app/state';
	import { useSessions } from '$lib/sessions/context.svelte';
	import { durationSeconds, formatDuration, statusLabel } from '$lib/domain/sessions/session';
	const sessions = useSessions();
	let session = $derived(sessions.find(page.params.id ?? ''));
	let section = $state('summary');
	$effect(() => {
		section = page.url.searchParams.get('tab') === 'evidence' ? 'evidence' : 'summary';
	});
</script>

{#snippet icon(path: string)}
	<svg class="detail-icon" viewBox="0 0 24 24" aria-hidden="true"><path d={path} /></svg>
{/snippet}

<svelte:head><title>Detalle de sesión · EndoSight</title></svelte:head>
{#if session}
	{#if section !== 'findings'}
	<p class="breadcrumb"><a class="text-link" href={resolve('/sessions')}>← Sesiones</a></p>
	<div class="page-heading support-heading detail-banner">
		<svg class="detail-wave" viewBox="0 0 1000 140" preserveAspectRatio="none" aria-hidden="true"><path d="M0 140Q100 45 230 116T435 78T615 62T820 57T1000 22V140Z" /><path d="M100 140Q240 93 350 125T570 95T780 112T1000 54V140Z" /></svg>
		<img src={colon} alt="" />
		<div class="detail-heading">
			<span class="detail-tile-icon">{@render icon('M6 3h8l4 4v14H6zM14 3v5h4M9 12h6m-6 4h6')}</span>
			<div>
			<h1>Detalle de sesión</h1>
			<p class="muted session-code">Sesión {session.id.slice(0, 8)} · {new Date(session.createdAt).toLocaleString('es-PE')}</p>
			</div>
		</div>
		<div class="detail-status">
			<span class="session-pill" class:session-finished={session.status === 'finished'}>{#if session.status === 'finished'}{@render icon('m5 12 4 4 10-10')}{/if}{statusLabel(session.status)}</span>
			{#if session.status === 'finished'}<span class="session-pill">{@render icon('M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18Zm0 4v5l4 2')}{formatDuration(durationSeconds(session))}</span>{/if}
		</div>
	</div>
	{/if}
	<div class="tabs session-tabs" class:compact-detail-tabs={section !== 'summary'} role="group" aria-label="Sección del detalle">
		<button aria-pressed={section === 'summary'} onclick={() => (section = 'summary')}
			>{@render icon('m3 8 9-5 9 5-9 5zM3 12l9 5 9-5M3 16l9 5 9-5')}Resumen</button
		><button aria-pressed={section === 'findings'} onclick={() => (section = 'findings')}
			>{@render icon('M20 20l-5-5M17 10a7 7 0 1 1-14 0 7 7 0 0 1 14 0Z')}Hallazgos</button
		><button aria-pressed={section === 'evidence'} onclick={() => (section = 'evidence')}
			>{@render icon('M3 5h18v14H3zM3 16l5-5 4 4 3-3 6 6')}Evidencia</button
		>
	</div>
	<section class:panel={section === 'summary'} class="session-detail-panel">
		{#if section === 'summary'}
			<div class="detail-heading">
				<span class="detail-tile-icon">{@render icon('M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18Zm0 8v5m0-8v.1')}</span>
				<div><h2>Resumen de la sesión</h2><p class="muted">Información general de la sesión de asistencia endoscópica.</p></div>
			</div>
			<dl class="definition-grid">
				<div>
					<span class="detail-tile-icon">{@render icon('M3 6h12v12H3zM15 10l6-4v12l-6-4')}</span>
					<dt>Fuente</dt>
					<dd>{session.sourceType === 'camera' ? 'Cámara / capturadora' : 'Archivo de prueba'}</dd>
				</div>
				<div>
					<span class="detail-tile-icon detail-start">{@render icon('m8 4 12 8-12 8z')}</span>
					<dt>Inicio de asistencia</dt>
					<dd>
						{session.startedAt
							? new Date(session.startedAt).toLocaleString('es-PE')
							: 'No iniciada'}
					</dd>
				</div>
				<div>
					<span class="detail-tile-icon detail-finish">{@render icon('M4 6h16v15H4zM8 3v6m8-6v6M4 11h16')}</span>
					<dt>Finalización</dt>
					<dd>
						{session.finishedAt
							? new Date(session.finishedAt).toLocaleString('es-PE')
							: 'Pendiente'}
					</dd>
				</div>
				<div>
					<span class="detail-tile-icon">{@render icon('M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18Zm0 4v5l4 2')}</span>
					<dt>Duración de sesión</dt>
					<dd>
						{session.status === 'finished'
							? formatDuration(durationSeconds(session))
							: 'Disponible al finalizar'}
					</dd>
				</div>
			</dl>
			<p class="detail-notice">{@render icon('M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18Zm0 8v5m0-8v.1')}El resumen y los recortes de detección se guardan en este navegador.</p>
			{:else if section === 'findings'}
				{#key session.id}<EvidenceRecords mode="findings" sessionId={session.id} />{/key}
			{:else}
				{#key session.id}<EvidenceRecords mode="evidence" sessionId={session.id} />{/key}
			{/if}
	</section>
{:else}<section class="panel empty-state">
		<h1>Sesión no disponible</h1>
		<p class="muted">
			No se encontró este registro en el historial de este navegador.
		</p>
		<a href={resolve('/sessions')} class="button">Volver a sesiones</a>
	</section>{/if}
