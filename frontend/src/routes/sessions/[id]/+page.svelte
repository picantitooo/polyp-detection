<script lang="ts">
	import { resolve } from '$app/paths';
	import { page } from '$app/state';
	import { useSessions } from '$lib/sessions/context.svelte';
	import { durationSeconds, formatDuration, statusLabel } from '$lib/sessions/model';
	const sessions = useSessions();
	let session = $derived(sessions.find(page.params.id ?? ''));
	let section = $state('summary');
</script>

<svelte:head><title>Detalle de sesión · Polyp</title></svelte:head>
{#if session}
	<p class="breadcrumb"><a href={resolve('/sessions')}>Sesiones</a> / {session.id.slice(0, 8)}</p>
	<div class="page-heading">
		<div>
			<h1>Detalle de sesión</h1>
			<p class="muted">{session.id}</p>
		</div>
		<span class="badge">{statusLabel(session.status)}</span>
	</div>
	<div class="tabs" role="group" aria-label="Sección del detalle">
		<button aria-pressed={section === 'summary'} onclick={() => (section = 'summary')}
			>Resumen</button
		><button aria-pressed={section === 'findings'} onclick={() => (section = 'findings')}
			>Hallazgos</button
		><button aria-pressed={section === 'evidence'} onclick={() => (section = 'evidence')}
			>Evidencia</button
		>
	</div>
	<section class="panel">
		{#if section === 'summary'}<h2>Resumen de la sesión</h2>
			<dl class="definition-grid">
				<div>
					<dt>Fuente</dt>
					<dd>{session.sourceType === 'camera' ? 'Cámara / capturadora' : 'Archivo de prueba'}</dd>
				</div>
				<div>
					<dt>Inicio de asistencia</dt>
					<dd>
						{session.startedAt
							? new Date(session.startedAt).toLocaleString('es-PE')
							: 'No iniciada'}
					</dd>
				</div>
				<div>
					<dt>Finalización</dt>
					<dd>
						{session.finishedAt
							? new Date(session.finishedAt).toLocaleString('es-PE')
							: 'Pendiente'}
					</dd>
				</div>
				<div>
					<dt>Duración de sesión</dt>
					<dd>
						{session.status === 'finished'
							? formatDuration(durationSeconds(session))
							: 'Disponible al finalizar'}
					</dd>
				</div>
			</dl>
			<p class="hint">Las sesiones se borran al recargar.</p>
			<button disabled>Exportar resumen</button>{:else}<div class="empty-state">
				<span class="badge">Pendiente</span>
				<h2>
					{section === 'findings' ? 'Revisión de hallazgos' : 'Evidencia'}
				</h2>
				<p class="muted">
					Esta sesión no conserva evidencia ni eventos. Aquí se incorporará su revisión en una
					siguiente versión.
				</p>
			</div>{/if}
	</section>
	<div class="actions">
		<a class="button" href={resolve('/sessions')}>Volver a sesiones</a><a
			class="button primary"
			href={resolve('/sessions/new')}>Nueva sesión</a
		>
	</div>
{:else}<section class="panel empty-state">
		<h1>Sesión no disponible</h1>
		<p class="muted">
			No existe en esta ejecución o la página se recargó. Los registros todavía no son persistentes.
		</p>
		<a href={resolve('/sessions')} class="button">Volver a sesiones</a>
	</section>{/if}
