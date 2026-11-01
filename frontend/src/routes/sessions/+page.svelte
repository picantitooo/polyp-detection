<script lang="ts">
	import { resolve } from '$app/paths';
	import { useSessions } from '$lib/sessions/context.svelte';
	import { statusLabel, durationSeconds, formatDuration } from '$lib/sessions/model';
	const sessions = useSessions();
</script>

<svelte:head><title>Sesiones · Polyp</title></svelte:head>
<div class="page-heading">
	<h1>Sesiones</h1>
	<a class="button primary" href={resolve('/sessions/new')}>Nueva sesión</a>
</div>
{#if sessions.records.length}
	<div class="table-wrap">
		<table class="sessions-table">
			<thead
				><tr
					><th scope="col">Sesión</th><th scope="col">Inicio</th><th scope="col">Fuente</th><th
						scope="col">Estado</th
					><th scope="col">Duración</th><th scope="col"
						><span class="visually-hidden">Acciones</span></th
					></tr
				></thead
			><tbody
				>{#each sessions.records as session (session.id)}<tr
						><td>{session.id.slice(0, 8)}</td><td
							>{new Date(session.createdAt).toLocaleString('es-PE')}</td
						><td>{session.sourceType === 'camera' ? 'Capturadora' : 'Video'}</td><td
							>{statusLabel(session.status)}</td
						><td
							>{session.status === 'finished' ? formatDuration(durationSeconds(session)) : '—'}</td
						><td
							><a
								class="text-link"
								aria-label={`Abrir sesión ${session.id.slice(0, 8)}`}
								href={resolve('/sessions/[id]', { id: session.id })}>Abrir</a
							></td
						></tr
					>{/each}</tbody
			>
		</table>
	</div>
{:else}<section class="empty-state">
		<h2>No hay sesiones</h2>
		<p class="muted">Crea una sesión para conectar la fuente de video.</p>
	</section>{/if}
<p class="hint session-retention">Las sesiones se borran al recargar la página.</p>
