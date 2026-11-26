<script lang="ts">
	import { onMount } from 'svelte';
	import colon from '$lib/assets/colon-detection.png';
	import { resolve } from '$app/paths';
	import { createClientId } from '$lib/utils/client-id';
	import { evidenceImage, listEvidence, listFindings, saveFinding, type Evidence, type Finding } from '$lib/sessions/evidence';

	let { mode, sessionId = '' }: { mode: 'evidence' | 'findings'; sessionId?: string } = $props();
	let evidence = $state<Evidence[]>([]);
	let findings = $state<Finding[]>([]);
	let chosenSession = $state('');
	let selected = $state<string[]>([]);
	let decision = $state<Finding['decision']>('Revisado');
	let note = $state('');
	let loading = $state(true);
	let saving = $state(false);
	let error = $state('');
	let query = $state('');
	let classification = $state('');
	let order = $state('recent');
	let pageSize = $state(10);
	let page = $state(1);
	let zoom = $state<Evidence | null>(null);
	let viewer = $state<HTMLDialogElement>(undefined!);
	let scope = $derived(sessionId || chosenSession);
	let availableSessions = $derived([...new Set(evidence.map((item) => item.sessionId))]);
	let scopedEvidence = $derived(evidence.filter((item) => !scope || item.sessionId === scope));
	let scopedFindings = $derived(findings.filter((item) => !scope || item.sessionId === scope));
	let unassigned = $derived(scopedEvidence.filter((item) =>
		!findings.some((finding) => finding.evidenceIds.includes(item.id))
	));
	let reviewed = $derived(scopedEvidence.length - unassigned.length);
	let filtered = $derived(scopedEvidence.filter((item) =>
		(!classification || item.label === classification) &&
		`${displayLabel(item.label)} ${item.sessionId}`.toLowerCase().includes(query.trim().toLowerCase())
	).sort((a, b) => order === 'confidence' ? b.confidence - a.confidence :
		(order === 'oldest' ? 1 : -1) * (Date.parse(a.capturedAt) - Date.parse(b.capturedAt))));
	let pageCount = $derived(Math.max(1, Math.ceil(filtered.length / pageSize)));
	let current = $derived(Math.min(page, pageCount));
	let visible = $derived(filtered.slice((current - 1) * pageSize, current * pageSize));

	function displayLabel(label: string) {
		return label === 'hiperplasico' ? 'Hiperplásico' : label === 'adenoma' ? 'Adenoma' : label;
	}

	function exportResults() {
		const quote = (value: string | number) => {
			const raw = String(value);
			const safe = /^[=+@\-\t\r\n]/.test(raw) ? "'" + raw : raw;
			return '"' + safe.replaceAll('"', '""') + '"';
		};
		const rows = [['Sesión', 'Fecha', 'Clasificación IA', 'Confianza (%)', 'Detección (%)'],
			...filtered.map((item) => [item.sessionId, item.capturedAt, displayLabel(item.label),
				Math.round(item.confidence * 100), Math.round(item.detectionConfidence * 100)])];
		const url = URL.createObjectURL(new Blob(['\uFEFF', rows.map((row) => row.map(quote).join(';')).join('\r\n')], { type: 'text/csv;charset=utf-8' }));
		const link = document.createElement('a');
		link.href = url;
		link.download = 'evidencias-endosight.csv';
		link.click();
		setTimeout(() => URL.revokeObjectURL(url), 1000);
	}

	onMount(() => {
		if (mode === 'evidence') pageSize = 5;
		Promise.all([listEvidence(), mode === 'findings' ? listFindings() : Promise.resolve([])])
			.then(([items, reviews]) => {
				evidence = items.sort((a, b) => Date.parse(b.capturedAt) - Date.parse(a.capturedAt));
				findings = reviews;
				chosenSession = '';
			})
			.catch(() => (error = 'No se pudo leer el registro local.'))
			.finally(() => (loading = false));
	});

	async function submit(event: SubmitEvent) {
		event.preventDefault();
		const reviewSession = scope || unassigned.find((item) => selected.includes(item.id))?.sessionId;
		if (!reviewSession) return;
		const evidenceIds = unassigned.filter((item) => item.sessionId === reviewSession && selected.includes(item.id)).map((item) => item.id);
		if (!evidenceIds.length || saving) return;
		saving = true;
		error = '';
		try {
			const finding = { id: createClientId(), sessionId: reviewSession, evidenceIds, decision, note: note.trim() };
			await saveFinding(finding);
			findings = [finding, ...findings];
			selected = [];
			note = '';
		} catch {
			error = 'No se pudo guardar la revisión.';
		} finally {
			saving = false;
		}
	}
</script>

{#snippet card(item: Evidence)}
	<img src={evidenceImage(item)} alt="Recorte de la región marcada por la IA" loading="lazy" />
	<div>
		<strong>{displayLabel(item.label)}</strong>
		<p class="hint">{new Date(item.capturedAt).toLocaleString('es-PE')}{item.videoSeconds !== null ? ` · ${Math.floor(item.videoSeconds)} s de señal` : ''}</p>
		<p class="hint">Clasificación IA {Math.round(item.confidence * 100)} % · Detección {Math.round(item.detectionConfidence * 100)} %</p>
	</div>
{/snippet}

{#if error}<p role="alert" class="error">{error}</p>{/if}
{#if loading}
	<p role="status">Cargando registros…</p>
{:else if !error || evidence.length}
	{#if !sessionId && availableSessions.length && mode === 'evidence'}
		<label>Sesión
			<select bind:value={chosenSession} onchange={() => (selected = [])} disabled={saving}>
				{#if mode === 'evidence'}<option value="">Todas las sesiones</option>{/if}
				{#each availableSessions as id (id)}<option value={id}>{id.slice(0, 8)}</option>{/each}
			</select>
		</label>
	{/if}
	{#if mode === 'evidence' && !sessionId}
		{#if !scopedEvidence.length}<p class="muted">Todavía no hay evidencias guardadas.</p>{/if}
		<ul class="evidence-grid">
			{#each scopedEvidence as item (item.id)}
				<li class="panel">{@render card(item)}{#if !sessionId}<a class="text-link" href={resolve('/sessions/[id]', { id: item.sessionId })}>Sesión {item.sessionId.slice(0, 8)}</a>{/if}</li>
			{/each}
		</ul>
	{:else}
		<div class:panel={!!sessionId} class="findings-results">
		<div class="findings-toolbar">
			<span class="detail-tile-icon" aria-hidden="true"><svg class="detail-icon" viewBox="0 0 24 24"><path d="M3 4h18v16H3zM3 17l5-5 4 4 3-3 6 6"/><circle cx="8" cy="8" r="1"/></svg></span>
			<div><h2>{mode === 'evidence' ? 'Evidencia de la sesión' : sessionId ? 'Hallazgos detectados' : 'Revisión de hallazgos'}</h2><p class="muted">{mode === 'evidence' ? 'Capturas relevantes del video con su información de análisis.' : 'Revisa, filtra y valida las detecciones identificadas por la IA.'}</p></div>
			<input type="search" aria-label={mode === 'evidence' ? 'Buscar evidencia' : 'Buscar hallazgo o sesión'} placeholder={mode === 'evidence' ? 'Buscar evidencia…' : 'Buscar hallazgo…'} bind:value={query} oninput={() => (page = 1)} />
			<select aria-label="Filtrar por clasificación" bind:value={classification} onchange={() => (page = 1)}>
				<option value="">Todas las clasificaciones</option>
				{#each [...new Set(scopedEvidence.map((item) => item.label))] as label (label)}<option value={label}>{displayLabel(label)}</option>{/each}
			</select>
			<select aria-label="Ordenar evidencias" bind:value={order} onchange={() => (page = 1)}>
				<option value="recent">Más recientes</option><option value="oldest">Más antiguas</option><option value="confidence">Mayor confianza</option>
			</select>
			{#if query || classification}<button onclick={() => { query = ''; classification = ''; page = 1; }}>Limpiar filtros</button>{/if}
			<button class:primary={!!sessionId} onclick={exportResults} disabled={!filtered.length}>↓ Exportar CSV</button>
		</div>
		<div class="findings-banner" class:session-findings-metrics={!!sessionId}>
			{#if !sessionId}
			<svg class="findings-wave" viewBox="0 0 1000 130" preserveAspectRatio="none" aria-hidden="true"><path d="M0 130H430C530 130 550 12 650 55S720 105 805 50 940 43 1000 75V130Z"/><path d="M440 130C560 130 630 12 730 26S820 98 910 50 970 37 1000 54V130Z"/></svg>
			<img src={colon} alt="" />
			<div class="findings-reviewed">Revisadas<strong>{reviewed}</strong><small>de {scopedEvidence.length} evidencias</small></div>
			{:else}
				<div>{mode === 'evidence' ? 'Total de evidencias' : 'Detecciones de la sesión'}<strong>{scopedEvidence.length}</strong></div>
			{/if}
			<div>Hiperplásico<strong>{scopedEvidence.filter((item) => item.label === 'hiperplasico').length}</strong></div>
			<div>Adenoma<strong>{scopedEvidence.filter((item) => item.label === 'adenoma').length}</strong></div>
		</div>
		{#if !visible.length}<p class="muted">{scopedEvidence.length ? 'No hay coincidencias.' : 'Todavía no hay evidencias para revisar.'}</p>{/if}
			<form onsubmit={submit}>
				<fieldset disabled={saving}>
					<legend class="visually-hidden">Selecciona recortes de la misma región para crear un hallazgo</legend>
					<div class="findings-grid">
						{#each visible as item (item.id)}
							<article class="panel finding-tile">
								<button type="button" class="finding-preview" aria-label="Ampliar captura" onclick={() => { zoom = item; viewer.showModal(); }}>
									<img src={evidenceImage(item)} alt="" loading="lazy" />
									<span aria-hidden="true">⌕</span>
									{#if item.videoSeconds !== null}<small>{Math.floor(item.videoSeconds)} s</small>{/if}
								</button>
								<strong class="session-pill" class:finding-adenoma={item.label === 'adenoma'}>{displayLabel(item.label)}</strong>
								<p class="hint">{new Date(item.capturedAt).toLocaleString('es-PE')}</p>
								{#if mode === 'evidence'}
									<p class="hint">Clasificación IA: {Math.round(item.confidence * 100)} %</p>
									<p class="hint">Detección: {Math.round(item.detectionConfidence * 100)} %</p>
								{:else}
								<p class="hint">Clasificación IA: {Math.round(item.confidence * 100)} % · Detección: {Math.round(item.detectionConfidence * 100)} %</p>
								{#if unassigned.includes(item)}
									<label class="finding-select"><input type="checkbox" bind:group={selected} value={item.id}
										disabled={selected.length > 0 && !scopedEvidence.some((other) => selected.includes(other.id) && other.sessionId === item.sessionId)} /> Seleccionar para revisión</label>
								{:else}<small>Con revisión guardada</small>{/if}
								{/if}
							</article>
						{/each}
					</div>
					{#if mode === 'findings' && selected.length}
					<div class="panel">
					<p>Agrupa recortes de la misma región en un hallazgo.</p>
					<label>Decisión
						<select bind:value={decision}><option>Revisado</option><option>Descartado</option><option>No concluyente</option></select>
					</label>
					<label>Observación <textarea bind:value={note} maxlength="1000" rows="3"></textarea></label>
					<button class="primary" disabled={!selected.length || saving}>Guardar hallazgo</button>
					</div>
					{/if}
				</fieldset>
			</form>
		<div class="history-footer findings-pagination">
			<span role="status">{filtered.length ? `Mostrando ${(current - 1) * pageSize + 1}–${(current - 1) * pageSize + visible.length} de ${filtered.length} evidencias` : '0 evidencias'}</span>
			<nav aria-label="Paginación de evidencias">
				<label class="findings-page-size">Por página <select aria-label="Evidencias por página" bind:value={pageSize} onchange={() => (page = 1)}><option value={5}>5</option><option value={10}>10</option><option value={20}>20</option></select></label>
				<button disabled={current <= 1} onclick={() => (page = current - 1)} aria-label="Página anterior">‹</button>
				{#each Array.from({ length: Math.min(3, pageCount) }, (_, index) => Math.max(1, Math.min(current - 1, pageCount - 2)) + index) as number (number)}
					<button class:primary={number === current} aria-current={number === current ? 'page' : undefined} aria-label={`Página ${number}`} onclick={() => (page = number)}>{number}</button>
				{/each}
				<button disabled={current >= pageCount} onclick={() => (page = current + 1)} aria-label="Página siguiente">›</button>
			</nav>
		</div>
		</div>
		{#if mode === 'findings' && scopedFindings.length}
		<details class="panel saved-findings-group" open>
		<summary>Hallazgos guardados</summary>
		{#each scopedFindings as finding (finding.id)}
			<details class="panel saved-finding">
				<summary>
					<strong>{finding.decision}</strong>
					<span class="session-pill">{finding.evidenceIds.length} {finding.evidenceIds.length === 1 ? 'evidencia' : 'evidencias'}</span>
					{#if !sessionId}<small>Sesión {finding.sessionId.slice(0, 8)}</small>{/if}
				</summary>
				{#if finding.note}<p>{finding.note}</p>{/if}
				<ul class="evidence-grid">
					{#each scopedEvidence.filter((item) => finding.evidenceIds.includes(item.id)) as item (item.id)}
						<li>{@render card(item)}</li>
					{/each}
				</ul>
			</details>
		{/each}
		</details>
		{/if}
	{/if}
	<p class="hint">{mode === 'evidence' ? 'Las capturas se guardan en este navegador.' : 'Los recortes y las revisiones se guardan en este navegador.'}</p>
{/if}
<dialog class="finding-viewer" bind:this={viewer} aria-label="Captura de evidencia" onclose={() => (zoom = null)}>
	<button onclick={() => viewer.close()}>Cerrar</button>
	{#if zoom}<img src={evidenceImage(zoom)} alt="Recorte de la región marcada por la IA" />{/if}
</dialog>
