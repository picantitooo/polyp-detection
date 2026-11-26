<script lang="ts">
	import { onMount } from 'svelte';
	import { resolve } from '$app/paths';
	import { useSessions } from '$lib/sessions/context.svelte';
	import { listEvidence, type Evidence } from '$lib/sessions/evidence';

	const sessions = useSessions();
	let captures = $state<Evidence[]>([]);
	let loading = $state(true);
	let failed = $state(false);
	let query = $state('');
	let date = $state('');
	let availability = $state('all');
	let descending = $state(true);
	const day = (value: string) => new Date(value).toLocaleDateString('es-PE');
	let counts = $derived(captures.reduce((result, capture) => {
		result.set(capture.sessionId, (result.get(capture.sessionId) ?? 0) + 1);
		return result;
	}, new Map<string, number>()));
	let dates = $derived([...new Set(sessions.records.map((session) => day(session.createdAt)))]);
	let rows = $derived(sessions.records.filter((session) => {
		const hasCaptures = counts.has(session.id);
		return session.id.toLowerCase().includes(query.trim().toLowerCase()) &&
			(!date || day(session.createdAt) === date) &&
			(availability === 'all' || hasCaptures === (availability === 'available'));
	}).sort((a, b) => (descending ? -1 : 1) * (Date.parse(a.createdAt) - Date.parse(b.createdAt))));

	onMount(() => {
		listEvidence().then((items) => (captures = items)).catch(() => (failed = true))
			.finally(() => (loading = false));
	});
</script>

{#snippet documentIcon()}
	<svg class="detail-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M3 4h18v16H3zM3 17l5-5 4 4 3-3 6 6"/><circle cx="8" cy="8" r="1"/></svg>
{/snippet}

<header class="page-heading support-heading detail-banner evidence-index-banner">
	<svg class="detail-wave" viewBox="0 0 1000 140" preserveAspectRatio="none" aria-hidden="true"><path d="M0 140H320Q380 140 470 80T640 84T820 88T1000 81V140Z" /></svg>
	<svg class="evidence-banner-art" viewBox="0 0 120 110" aria-hidden="true">
		<g transform="rotate(14 76 61)"><rect x="51" y="22" width="56" height="82" rx="6" /><path d="M62 37h34m-34 10h34m-34 10h34"/></g>
		<g transform="rotate(-10 47 51)"><rect x="13" y="9" width="66" height="90" rx="7"/><rect x="24" y="24" width="44" height="35" rx="4"/><path d="m24 53 12-12 9 9 7-7 16 15M24 70h43m-43 10h36"/><circle cx="54" cy="34" r="4"/></g>
	</svg>
	<div><h1>Evidencia de las sesiones</h1><p class="muted">Consulta las capturas guardadas durante la asistencia endoscópica.</p></div>
</header>

<div class="history-metrics evidence-index-metrics">
	{#each [
		['Sesiones registradas', sessions.records.length],
		['Evidencias guardadas', loading || failed ? '—' : captures.length],
		['Sesiones con evidencia', loading || failed ? '—' : sessions.records.filter((session) => counts.has(session.id)).length]
	] as [label, total] (label)}
		<div class="history-metric"><span class="detail-tile-icon">{@render documentIcon()}</span><div>{label}<strong>{total}</strong></div></div>
	{/each}
</div>

<section class="panel session-history" aria-labelledby="evidence-index-title">
	<div class="history-toolbar">
		<div><h2 class="home-card-title" id="evidence-index-title">{@render documentIcon()}Evidencia por sesión</h2><p class="muted">Abre una sesión para ver sus capturas y datos de detección.</p></div>
		<a class="button primary" href={resolve('/sessions/new')}>＋ Nueva sesión</a>
	</div>
	<div class="evidence-index-filters">
		<input type="search" aria-label="Buscar por ID de sesión" placeholder="Buscar por ID de sesión…" bind:value={query} />
		<select aria-label="Filtrar por fecha" bind:value={date}>
			<option value="">Todas las fechas</option>
			{#each dates as item (item)}<option value={item}>{item}</option>{/each}
		</select>
		<select aria-label="Filtrar por disponibilidad de evidencia" bind:value={availability}>
			<option value="all">Todos los estados</option><option value="available">Con evidencia</option><option value="empty">Sin evidencia</option>
		</select>
	</div>
	{#if loading}
		<p role="status">Cargando evidencias…</p>
	{:else if failed}
		<p class="error" role="alert">No se pudieron leer las capturas de este navegador.</p>
	{:else if rows.length}
		<div class="table-wrap" role="region" aria-label="Evidencia por sesión">
			<table class="sessions-table">
				<thead><tr><th scope="col" aria-sort={descending ? 'descending' : 'ascending'}><button class="history-sort" onclick={() => (descending = !descending)}>Fecha y hora <span aria-hidden="true">{descending ? '↓' : '↑'}</span></button></th><th scope="col">Sesión</th><th scope="col">Evidencias</th><th scope="col">Estado</th><th scope="col">Detalle</th></tr></thead>
				<tbody>
					{#each rows as session (session.id)}
						{@const detail = resolve('/sessions/[id]', { id: session.id })}
						{@const count = counts.get(session.id) ?? 0}
						<tr>
							<td>{new Date(session.createdAt).toLocaleString('es-PE')}</td>
							<td><a class="text-link" href={detail}>Sesión {session.id.slice(0, 8)}</a></td>
							<td><span class="session-pill">{count} {count === 1 ? 'captura' : 'capturas'}</span></td>
							<td><span class="session-pill" data-tone={count ? 'finished' : undefined}>{count ? 'Disponible' : 'Sin evidencia'}</span></td>
							<td>{#if count}<a class="button session-open" href={detail + '?tab=evidence'}>Ver evidencia</a>{:else}—{/if}</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
		<p class="history-footer" role="status">Mostrando {rows.length} de {sessions.records.length} sesiones</p>
	{:else}
		<p class="dashboard-empty">{sessions.records.length ? 'No hay sesiones que coincidan con los filtros.' : 'Aún no hay sesiones registradas.'}</p>
	{/if}
</section>
