<script lang="ts">
	import colon from '$lib/assets/colon-detection.png';
	import { resolve } from '$app/paths';
	import { useSessions } from '$lib/sessions/context.svelte';
	import { statusLabel } from '$lib/domain/sessions/session';
	const sessions = useSessions();
</script>

<svelte:head><title>Inicio · EndoSight</title></svelte:head>
<div class="home-content">
	<section class="dashboard-welcome"><div><h1>Gestión de sesiones</h1><p>Prepara la señal de video y consulta las sesiones de asistencia endoscópica.</p><div class="actions"><a class="button primary" href={resolve('/sessions/new')}>Nueva sesión</a><a class="button hero-secondary" href={resolve('/sessions')}>Ver sesiones</a></div></div><img class="dashboard-colon" src={colon} alt=""/></section>
 <div class="metric-grid">{#each ['prepared','active','finished'] as status}<section class="panel metric-card"><div><span>{status === 'prepared' ? 'En preparación' : status === 'active' ? 'En curso' : 'Finalizadas'}</span><strong>{sessions.records.filter(record => record.status === status).length}</strong></div></section>{/each}</div>
 <div class="home-lower">
	<section class="panel">
		<div class="page-heading"><h2 class="home-card-title"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M12 7v5l4 2" /></svg>Sesiones recientes</h2><a class="text-link" href={resolve('/sessions')}>Ver historial <span aria-hidden="true">→</span></a></div>
		{#if sessions.records.length}
			<ul class="recent-sessions">
				{#each sessions.records.slice(0, 6) as session (session.id)}
					<li>
						<div>
							<a class="text-link" href={resolve('/sessions/[id]', { id: session.id })}>Sesión {session.id.slice(0, 8)}</a>
							<p class="hint">{new Date(session.createdAt).toLocaleString('es-PE')} · {session.sourceType === 'camera' ? 'Capturadora' : 'Video'}</p>
						</div>
						<span class="badge">{statusLabel(session.status)}</span>
					</li>
				{/each}
			</ul>
		{:else}
			<div class="dashboard-empty">
				<svg class="empty-monitor" viewBox="0 0 64 56" aria-hidden="true"><rect x="3" y="3" width="58" height="39" rx="7" /><path d="m27 14 15 9-15 9zM32 42v9m-12 0h24" /></svg>
				<h2>Aún no hay sesiones</h2><p class="muted">El historial aparecerá aquí tras registrar una sesión.</p>
			</div>
		{/if}
	</section>
	<aside class="panel workflow"><h2>Revisión de sesiones</h2><div class="actions"><a class="button" href={resolve('/findings')}>Revisar hallazgos</a><a class="button" href={resolve('/reports')}>Abrir informes</a></div></aside></div>
	<p class="hint">Prototipo de investigación. La asistencia visual no sustituye el criterio clínico.</p>
</div>
