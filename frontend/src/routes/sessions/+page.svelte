<script lang="ts">
	import { resolve } from '$app/paths';
	import { page } from '$app/state';
	import colon from '$lib/assets/colon-detection.png';
	import { useSessions } from '$lib/sessions/context.svelte';
	import { durationSeconds, formatDuration, type SessionStatus } from '$lib/domain/sessions/session';

	const sessions = useSessions();
	const labels = { finished: 'Finalizada', active: 'En progreso', prepared: 'Pendiente' };
	const calendar = 'M4 6h16v15H4zM8 3v6m8-6v6M4 11h16';
	const states = [
		{ key: 'finished', label: 'Finalizadas', icon: 'm4 12 5 5L20 6' },
		{ key: 'active', label: 'En progreso', icon: 'm8 4 12 8-12 8z' },
		{ key: 'prepared', label: 'Pendientes', icon: 'M9 5v14m6-14v14' }
	] as const;

	let query = $state('');
	let filter = $state<SessionStatus | 'all'>('all');
	let selectedPage = $state(1);
	let newestFirst = $state(true);
	const pageSize = 4;
	let records = $derived(sessions.records.filter((record) =>
		(filter === 'all' || record.status === filter) &&
		`${record.id} ${sourceLabel(record.sourceType)}`.toLowerCase().includes(query.trim().toLowerCase())
	).sort((a, b) => (newestFirst ? -1 : 1) * (Date.parse(a.createdAt) - Date.parse(b.createdAt))));
	let pages = $derived(Math.max(1, Math.ceil(records.length / pageSize)));
	let current = $derived(Math.min(selectedPage, pages));
	let visible = $derived(records.slice((current - 1) * pageSize, current * pageSize));
	let pageNumbers = $derived(Array.from({ length: Math.min(3, pages) }, (_, index) =>
		Math.max(1, Math.min(current - 1, pages - 2)) + index
	));

	function sourceLabel(source: 'camera' | 'file') {
		return source === 'camera' ? 'Cámara / capturadora' : 'Archivo de video';
	}
</script>

{#snippet icon(path: string)}
	<svg class="detail-icon" viewBox="0 0 24 24" aria-hidden="true"><path d={path} /></svg>
{/snippet}

{#snippet metric(label: string, value: number, tone: string, path: string)}
	<div class="history-metric" data-tone={tone}>
		<span class="detail-tile-icon">{@render icon(path)}</span>
		<div>{label}<strong>{value}</strong></div>
		<svg class="history-metric-wave" viewBox="0 0 100 42" aria-hidden="true">
			<defs><linearGradient id={`session-wave-${tone}`} x2="0%" y2="100%"><stop stop-color="currentColor" stop-opacity=".26" /><stop offset="1" stop-color="currentColor" stop-opacity="0" /></linearGradient></defs>
			<path fill={`url(#session-wave-${tone})`} stroke="none" d="M1 39C17 39 19 16 39 22S69 37 99 3V42H1Z" />
			<path d="M1 39C17 39 19 16 39 22S69 37 99 3" />
		</svg>
	</div>
{/snippet}

<svelte:head><title>Sesiones · EndoSight</title></svelte:head>
{#if page.route.id === '/sessions'}
	<header class="page-heading support-heading detail-banner history-banner">
		<svg class="detail-wave" viewBox="0 0 1000 140" preserveAspectRatio="none" aria-hidden="true"><path d="M0 140Q240 140 295 108T408 52T536 73T694 59T840 56T1000 92V140Z" /></svg>
		<img src={colon} alt="" />
		<div><h1>Sesiones</h1><p class="muted">Consulta y gestiona el historial de asistencias endoscópicas.</p></div>
		<a class="button primary" href={resolve('/sessions/new')}>＋ Nueva sesión</a>
	</header>
	<div class="history-metrics" aria-label="Resumen de sesiones">
		{@render metric('Total de sesiones', sessions.records.length, 'total', calendar)}
		{#each states as state (state.key)}
			{@render metric(state.label, sessions.records.filter((record) => record.status === state.key).length, state.key, state.icon)}
		{/each}
	</div>
	<section class="panel session-history" aria-labelledby="history-title">
		<div class="history-toolbar">
			<h2 id="history-title" class="home-card-title">{@render icon(calendar)} Historial de sesiones</h2>
			<div class="history-filters">
				<label class="visually-hidden" for="history-query">Buscar por sesión o fuente</label>
				<div class="history-search">
					{@render icon('M20 20l-5-5M17 10a7 7 0 1 1-14 0 7 7 0 0 1 14 0Z')}
					<input id="history-query" type="search" placeholder="Buscar por sesión o fuente…" bind:value={query} oninput={() => (selectedPage = 1)} />
				</div>
				<div class="history-status-filter">
					{@render icon('M3 5h18l-7 8v5l-4 2v-7z')}
					<label class="visually-hidden" for="history-filter">Filtrar por estado</label>
					<select id="history-filter" bind:value={filter} onchange={() => (selectedPage = 1)}>
						<option value="all">Todos los estados</option>
						{#each states as state (state.key)}<option value={state.key}>{state.label}</option>{/each}
					</select>
					<svg class="history-filter-chevron detail-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="m7 10 5 5 5-5" /></svg>
				</div>
			</div>
		</div>
		{#if visible.length}
			<div class="table-wrap">
				<table class="sessions-table">
					<thead><tr><th scope="col">Sesión</th><th scope="col" aria-sort={newestFirst ? 'descending' : 'ascending'}><button class="history-sort" onclick={() => { newestFirst = !newestFirst; selectedPage = 1; }}>Creada <span aria-hidden="true">{newestFirst ? '↓' : '↑'}</span></button></th><th scope="col">Fuente</th><th scope="col">Estado</th><th scope="col">Duración</th><th scope="col">Acciones</th></tr></thead>
					<tbody>
						{#each visible as session (session.id)}
							<tr>
								<td>{session.id.slice(0, 8)}</td>
								<td>{new Date(session.createdAt).toLocaleString('es-PE')}</td>
								<td><span class="history-cell-icon">{@render icon(session.sourceType === 'camera' ? 'M3 7h4l2-3h6l2 3h4v13H3zM16 13a4 4 0 1 1-8 0 4 4 0 0 1 8 0Z' : 'M3 5h7l2 3h9v12H3z')}{sourceLabel(session.sourceType)}</span></td>
								<td><span class="session-pill history-cell-icon" data-tone={session.status}>{@render icon(states.find((item) => item.key === session.status)?.icon ?? calendar)}{labels[session.status]}</span></td>
								<td>{session.status === 'finished' ? formatDuration(durationSeconds(session)) : '—'}</td>
								<td><a class="button session-open" aria-label={`Ver detalle de sesión ${session.id.slice(0, 8)}`} href={resolve('/sessions/[id]', { id: session.id })}>{@render icon('M2 12s4-6 10-6 10 6 10 6-4 6-10 6-10-6-10-6Zm13 0a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z')}Ver detalle</a></td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		{:else}
			<div class="dashboard-empty"><h3>{sessions.records.length ? 'No hay coincidencias' : 'Aún no hay sesiones'}</h3><p class="muted">{sessions.records.length ? 'Prueba otra búsqueda o cambia el filtro.' : 'Crea una sesión para conectar la fuente de video.'}</p>{#if sessions.records.length}<button onclick={() => { query = ''; filter = 'all'; selectedPage = 1; }}>Limpiar filtros</button>{/if}</div>
		{/if}
		<footer class="history-footer">
			<span role="status">Mostrando {visible.length} de {records.length} sesiones</span>
			{#if pages > 1}
				<nav aria-label="Páginas del historial">
					<button aria-label="Página anterior" disabled={current === 1} onclick={() => (selectedPage = current - 1)}>‹</button>
					{#each pageNumbers as number (number)}
						<button class:primary={number === current} aria-current={number === current ? 'page' : undefined} aria-label={`Página ${number}`} onclick={() => (selectedPage = number)}>{number}</button>
					{/each}
					<button aria-label="Página siguiente" disabled={current === pages} onclick={() => (selectedPage = current + 1)}>›</button>
				</nav>
			{/if}
		</footer>
	</section>
{/if}
