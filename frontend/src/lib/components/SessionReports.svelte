<script lang="ts">
	import { onMount } from 'svelte';
	import waves from '$lib/assets/illustrations/banner-waves.svg';
	import documents from '$lib/assets/illustrations/report-documents.svg';
	import { resolve } from '$app/paths';
	import { useSessions } from '$lib/sessions/context.svelte';
	import { durationSeconds, formatDuration, statusLabel } from '$lib/domain/sessions/session';
	import { addReport, evidenceImage, listEvidence, listFindings, listReports, saveReport, type Evidence, type Finding } from '$lib/sessions/evidence';
	import { createClientId } from '$lib/utils/client-id';
	import { reportLabels, reviewLabels, reviewComplete, type ReviewDecision, type SessionReport } from '$lib/application/sessions/session-report';

	const sessions = useSessions();
	let evidence = $state<Evidence[]>([]);
	let findings = $state<Finding[]>([]);
	let reports = $state<SessionReport[]>([]);
	let draft = $state<SessionReport | null>(null);
	let saving = $state(false);
	let dirty = $state(false);
	let message = $state('');
	let newestFirst = $state(true);
	let confirmFinal = $state(false);
	let listPage = $state(1);
	let query = $state('');
	let filter = $state('');
	let loading = $state(true);
	let failed = $state(false);
	let rows = $derived(reports.filter((item) =>
		(!filter || item.status === filter) && `${item.id} ${item.session.id}`.toLowerCase().includes(query.trim().toLowerCase())
	).sort((a, b) => (newestFirst ? -1 : 1) * a.createdAt.localeCompare(b.createdAt)));
	let listPages = $derived(Math.max(1, Math.ceil(rows.length / 8)));
	let currentListPage = $derived(Math.min(listPage, listPages));
	let listRows = $derived(rows.slice((currentListPage - 1) * 8, currentListPage * 8));
	let session = $derived(draft?.session);
	let captures = $derived(evidence.filter((item) => draft?.evidenceIds.includes(item.id))
		.sort((a, b) => Date.parse(b.capturedAt) - Date.parse(a.capturedAt)));
	let reviews = $derived(findings.filter((item) => draft?.reviewIds?.includes(item.id)));
	let reviewedCount = $derived(captures.filter((item) =>
		(draft?.validations[item.id]?.decision ?? 'pending') !== 'pending').length);
	let highlighted = $derived(captures.filter((item) => {
		const group = reviews.find((review) => review.evidenceIds.includes(item.id));
		return !group || captures.find((capture) => group.evidenceIds.includes(capture.id))?.id === item.id;
	}).slice(0, 5));
	let enlarged = $state<Evidence | null>(null);
	let viewer = $state<HTMLDialogElement>(undefined!);

	onMount(() => {
		Promise.all([listEvidence(), listFindings(), listReports()])
			.then(async ([items, saved, stored]) => {
				evidence = items;
				findings = saved;
				const existing = new Set(stored.map((report) => report.session.id));
				for (const source of sessions.records) {
					if (source.status !== 'finished' || existing.has(source.id)) continue;
					const now = new Date().toISOString();
					try {
						await addReport({
							id: 'INF-' + createClientId(), session: { ...source },
							evidenceIds: items.filter((item) => item.sessionId === source.id).map((item) => item.id),
							reviewIds: saved.filter((item) => item.sessionId === source.id).map((item) => item.id),
							validations: {}, observations: '', createdAt: now, updatedAt: now, status: 'draft'
						});
					} catch (error) {
						if (!(error instanceof DOMException && error.name === 'ConstraintError')) throw error;
					}
				}
				reports = await listReports();
			})
			.catch(() => (failed = true))
			.finally(() => (loading = false));
	});

	function selectReport(report: SessionReport) {
		if (saving || (dirty && !window.confirm('¿Descartar los cambios que no se han guardado?'))) return;
		draft = structuredClone($state.snapshot(report));
		dirty = false;
		confirmFinal = false;
		message = '';
	}

	async function persist(report: SessionReport, status = report.status) {
		if (saving) return;
		saving = true;
		const next: SessionReport = { ...report, status, updatedAt: new Date().toISOString() };
		try {
			await saveReport($state.snapshot(next));
			reports = [...reports.filter((item) => item.id !== next.id), next];
			draft = next;
			dirty = false;
			confirmFinal = false;
			message = 'Informe guardado.';
		} catch {
			message = 'No se pudo guardar el informe en este navegador.';
		} finally {
			saving = false;
		}
	}

	function closeReport() {
		if (saving || (dirty && !window.confirm('¿Descartar los cambios que no se han guardado?'))) return;
		draft = null;
		dirty = false;
		message = '';
	}

	let editor: HTMLDialogElement;
 let editing = $state<Evidence | null>(null);
 let decision = $state<ReviewDecision>('pending');
 let note = $state('');
 function openReview(item: Evidence) {
  editing = item;
  decision = draft?.validations[item.id]?.decision ?? 'pending';
  note = draft?.validations[item.id]?.note ?? '';
  editor.showModal();
 }
 function validate(id: string, changes: Partial<SessionReport['validations'][string]>) {
		if (!draft || draft.status === 'final' || saving) return;
		const prior = draft.validations[id] ?? { decision: 'pending', note: '' };
		draft.validations[id] = { ...prior, ...changes };
		draft.status = 'draft';
		dirty = true;
		confirmFinal = false;
	}

	function openCapture(item: Evidence) {
		enlarged = item;
		viewer.showModal();
	}

	function label(value: string) {
		return value === 'hiperplasico' ? 'Hiperplásico' : value === 'adenoma' ? 'Adenoma' : value;
	}
</script>

{#snippet fileIcon()}
	<svg class="detail-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M5 3h9l5 5v13H5zM14 3v6h5M8 13h8m-8 4h8" /></svg>
{/snippet}
{#snippet listIcon(path: string)}
	<svg class="detail-icon" viewBox="0 0 24 24" aria-hidden="true"><path d={path} /></svg>
{/snippet}
{#snippet statistic(label: string, value: number, icon: string, tone: string)}
	<div data-tone={tone}><span class="report-list-icon">{@render listIcon(icon)}</span><div><dt>{label}</dt><dd>{loading || failed ? '—' : value}</dd></div></div>
{/snippet}

<div class="session-reports report-single-view">
	{#if !draft}
	<section class="report-picker" aria-labelledby="reports-heading">
		<header class="reports-list-banner">
			<img src={waves} alt="" class="reports-list-waves" />
			<img src={documents} alt="" class="reports-list-art" />
			<span class="report-list-icon">{@render fileIcon()}</span>
			<div><h1 id="reports-heading">Informes</h1><p>Consulta y exporta los informes de asistencia endoscópica.</p></div>
		</header>
		<dl class="report-stats">
			{@render statistic('Total de informes', reports.length, 'm2 8 10-5 10 5-10 5zM2 12l10 5 10-5M2 16l10 5 10-5', 'total')}
			{@render statistic('Borradores', reports.filter((item) => item.status === 'draft').length, 'm4 16 12-12a2 2 0 0 1 4 4L8 20H4zM14 6l4 4', 'draft')}
			{@render statistic('Finalizados', reports.filter((item) => item.status === 'final').length, 'M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0ZM8 12l3 3 5-6', 'final')}
		</dl>
		<div class="report-filters">
			<div>{@render listIcon('M20 20l-5-5M17 10a7 7 0 1 1-14 0 7 7 0 0 1 14 0Z')}<input type="search" aria-label="Buscar por código de informe o sesión" placeholder="Buscar por código de informe o sesión…" bind:value={query} oninput={() => (listPage = 1)} /></div>
			<div>{@render listIcon('M3 4h7l10 10-6 6L3 9zM7 8h.01')}
			<select aria-label="Filtrar por estado del informe" bind:value={filter} onchange={() => (listPage = 1)}>
				<option value="">Todos los estados</option><option value="draft">Borrador</option><option value="reviewed">Revisado</option><option value="final">Finalizado</option>
			</select>
			</div>
			<div>{@render listIcon('M3 5h18v16H3zM7 3v4m10-4v4M3 10h18')}
			<select aria-label="Ordenar por fecha de generación" bind:value={newestFirst} onchange={() => (listPage = 1)}>
				<option value={true}>Más recientes primero</option><option value={false}>Más antiguos primero</option>
			</select>
			</div>
		</div>
		{#if loading}<p class="report-list-empty" role="status">Cargando informes…</p>
		{:else if failed}<p class="error" role="alert">No se pudieron leer los informes guardados.</p>
		{:else if listRows.length}
			<div class="table-wrap report-table-wrap">
				<table class="sessions-table report-table">
					<colgroup><col class="report-col-identity" /><col class="report-col-session" /><col class="report-col-date" /><col class="report-col-state" /><col /></colgroup>
					<thead><tr><th scope="col">Informe</th><th scope="col">Sesión</th><th scope="col">Fecha de generación</th><th scope="col">Estado</th><th scope="col">Acciones</th></tr></thead>
					<tbody>
						{#each listRows as item (item.id)}
							<tr>
								<th scope="row"><div class="report-identity"><span class="report-list-icon">{@render fileIcon()}</span><strong title={item.id}>{item.id.slice(0, 12)}</strong></div></th>
								<td><span class="session-pill">Sesión {item.session.id.slice(0, 8)}</span></td>
								<td><span class="report-generation">{@render listIcon('M3 5h18v16H3zM7 3v4m10-4v4M3 10h18')}<time datetime={item.createdAt}>{new Date(item.createdAt).toLocaleString('es-PE')}</time></span></td>
								<td><span class="session-pill report-status" data-status={item.status}>{reportLabels[item.status]}</span></td>
								<td><div class="report-row-actions"><button class="report-detail-button" aria-label={`Ver detalle del informe de la sesión ${item.session.id.slice(0, 8)}`} onclick={() => selectReport(item)}>{@render listIcon('M2 12s4-6 10-6 10 6 10 6-4 6-10 6-10-6-10-6Zm13 0a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z')}Ver detalle</button><details><summary aria-label="Más acciones">⋮</summary><button onclick={() => selectReport(item)}>Abrir informe</button></details></div></td>
							</tr>
						{/each}
					</tbody>
				</table>
				<p class="report-table-count" role="status">Mostrando {listRows.length} de {rows.length} informes</p>
			</div>
		{:else}
			<div class="report-list-empty" role="status">
				<strong>{reports.length ? 'No hay resultados' : 'Aún no hay informes'}</strong>
				<p class="muted">{reports.length ? 'Cambia la búsqueda o el filtro de estado.' : 'Los informes se crean automáticamente para las sesiones finalizadas.'}</p>
			</div>
		{/if}
		{#if listPages > 1}
			<nav class="history-footer" aria-label="Páginas de informes">
				<button disabled={currentListPage === 1} onclick={() => (listPage = currentListPage - 1)}>Anterior</button>
				<span role="status">Página {currentListPage} de {listPages}</span>
				<button disabled={currentListPage === listPages} onclick={() => (listPage = currentListPage + 1)}>Siguiente</button>
			</nav>
		{/if}
		{#if message}<p role="status">{message}</p>{/if}
	</section>
	{:else}
	<nav class="report-edit report-breadcrumb" aria-label="Ubicación del informe">
		<button class="text-button" onclick={closeReport} disabled={saving}>← Volver a informes</button>
		<span aria-hidden="true">›</span>
		<span aria-current="page">Informe {draft.id.slice(0, 12)}</span>
	</nav>
	{#if message}<p class="report-edit" role="status">{message}</p>{/if}

	<article class="report-document" aria-labelledby="report-title">
		{#if session && draft}
			<header class="report-document-header">
				<div class="detail-heading">{@render fileIcon()}<div><h2 id="report-title">Informe {draft.id.slice(0, 12)}</h2><p class="muted"><a href={resolve('/sessions/[id]', { id: session.id })}>Sesión {session.id.slice(0, 8)}</a> · {session.sourceType === 'camera' ? 'Capturadora' : 'Archivo de video'} · {new Date(draft.createdAt).toLocaleString('es-PE')}</p></div></div>
				<span class="session-pill" class:session-finished={draft.status === 'final'}>{reportLabels[draft.status]}</span>
				<button class="button report-print" onclick={() => window.print()} disabled={dirty || saving || loading || failed}>Imprimir / Guardar como PDF</button>
			</header>
			<div class="panel report-sheet">
			<div class="report-brand print-brand">
				<div class="detail-heading"><span class="detail-tile-icon">{@render fileIcon()}</span><div><strong>EndoSight</strong><small>Asistencia endoscópica</small></div></div>
				<div><b>Informe de colonoscopia</b><span>N.º {draft.id}</span><time datetime={draft.createdAt}>{new Date(draft.createdAt).toLocaleString('es-PE')}</time></div>
			</div>
			<div class="report-overview report-procedure">
				<section class="report-block">
					<h3>Datos del procedimiento</h3>
					<dl><dt>Tipo</dt><dd>Colonoscopia</dd><dt>Inicio</dt><dd>{session.startedAt ? new Date(session.startedAt).toLocaleString('es-PE') : 'No iniciado'}</dd><dt>Finalización</dt><dd>{session.finishedAt ? new Date(session.finishedAt).toLocaleString('es-PE') : 'No disponible'}</dd><dt>Duración</dt><dd>{formatDuration(durationSeconds(session))}</dd><dt>Fuente</dt><dd>{session.sourceType === 'camera' ? 'Cámara / capturadora' : 'Archivo de video'}</dd><dt>Estado</dt><dd><span class="session-pill" class:session-finished={session.status === 'finished'}>{statusLabel(session.status)}</span></dd></dl>
				</section>
				<section class="report-block report-ai">
					<h3>{@render fileIcon()} Hallazgos (detección por IA)</h3>
					<div class="findings-banner session-findings-metrics">
						<div>Total de capturas<strong>{loading || failed ? '—' : captures.length}</strong></div>
						<div>Hiperplásico<strong>{loading || failed ? '—' : captures.filter((item) => item.label === 'hiperplasico').length}</strong></div>
						<div>Adenoma<strong>{loading || failed ? '—' : captures.filter((item) => item.label === 'adenoma').length}</strong></div>
					</div>
				</section>
			</div>
			{#if loading}<p role="status">Cargando evidencias y revisiones…</p>
			{:else if failed}<p class="error" role="alert">No se pudieron leer las evidencias y revisiones de este navegador.</p>
			{:else}
				<section class="report-block">
					<h3>{@render fileIcon()} Revisión de capturas</h3><p>{reviewedCount} de {captures.length} capturas revisadas</p>{#if draft.status !== 'final' && reviewedCount < captures.length}<button class="report-edit" onclick={() => { const next = captures.find(item => (draft?.validations[item.id]?.decision ?? 'pending') === 'pending'); if (next) openReview(next); }}>Revisar siguiente pendiente</button>{/if}
					{#if captures.length}
						<div class="table-wrap">
							<table class="sessions-table capture-review-table">
								<thead><tr><th scope="col">#</th><th scope="col">Predicción IA</th><th scope="col">Clasificación / detección</th><th scope="col">Tiempo en señal</th><th scope="col">Evidencia</th><th scope="col">Revisión médica</th></tr></thead>
								<tbody>{#each captures as item, index (item.id)}
									<tr>
										<td>{index + 1}</td><td><span class="session-pill">{label(item.label)}</span></td>
										<td><small>Clasificación {Math.round(item.confidence * 100)} %</small><small>Detección {Math.round(item.detectionConfidence * 100)} %</small></td>
										<td><span class="mobile-time">Señal · </span>{item.videoSeconds === null ? '—' : `${item.videoSeconds.toFixed(2)} s`}</td>
										<td><button class="text-button" onclick={() => openCapture(item)}>Ver captura</button><span class="print-capture-ref">Captura {index + 1}</span></td>
										<td>
											<div>{reviewLabels[draft.validations[item.id]?.decision ?? 'pending']}</div>
											{#if draft.validations[item.id]?.note}<p class="print-capture-ref">{draft.validations[item.id].note}</p>{/if}
											{#if draft.status !== 'final'}
												<button class="report-edit" onclick={() => openReview(item)}>Revisar</button>
											{/if}
										</td>
									</tr>
								{/each}</tbody>
							</table>
						</div>
					{:else}<p class="muted">Esta sesión no tiene detecciones guardadas.</p>{/if}
				</section>
				{#if captures.length}
					<section class="report-block">
						<h3>{@render fileIcon()} Evidencia destacada</h3>
						<div class="report-captures">
							{#each highlighted as item (item.id)}
								<div><button class="finding-preview" aria-label="Ampliar captura" onclick={() => openCapture(item)}><img src={evidenceImage(item)} alt="" /></button><span class="session-pill">#{captures.indexOf(item) + 1} · {label(item.label)}</span><p class="hint">{item.videoSeconds === null ? 'Tiempo no disponible' : `${item.videoSeconds.toFixed(2)} s`} · {Math.round(item.confidence * 100)} % / {Math.round(item.detectionConfidence * 100)} %</p></div>
							{/each}
						</div>
						<a class="text-link report-evidence-link" href={resolve('/sessions/[id]', { id: session.id }) + '?tab=evidence'}>Ver todas las evidencias</a>
					</section>
				{/if}
				<section class="report-block report-review">
					<h3>{@render fileIcon()} Conclusión</h3>
					<p>Se incluyeron {captures.length} capturas de detección. La IA sugirió {captures.filter((item) => item.label === 'hiperplasico').length} como hiperplásico y {captures.filter((item) => item.label === 'adenoma').length} como adenoma. Estas cifras contabilizan capturas, no lesiones únicas.</p>
					<p>Validación del informe: {reviewedCount} revisadas y {captures.length - reviewedCount} pendientes. Revisiones agrupadas de la sesión: {reviews.length}.</p>
					{#each reviews as review (review.id)}
						<p><strong>{review.decision}</strong> · {review.evidenceIds.length} capturas{review.note ? ' — ' + review.note : ''}</p>
					{/each}
					{#if draft.observations}<p><strong>Observaciones del informe:</strong> {draft.observations}</p>{/if}
					{#if draft.status !== 'final'}
						<label class="report-edit">Observaciones del informe<textarea id="report-observations" placeholder="Añadir observaciones (opcional)" value={draft.observations} maxlength="2000" disabled={saving} oninput={(event) => {
							if (!draft) return;
							draft.observations = event.currentTarget.value;
							draft.status = 'draft';
							dirty = true;
							confirmFinal = false;
						}}></textarea></label>
					{/if}
					<p>Los resultados presentados corresponden a un sistema de asistencia basado en inteligencia artificial y no sustituyen la evaluación ni el criterio del especialista.</p>
				</section>
				<section class="report-block"><h3>{@render fileIcon()} Notas y trazabilidad</h3><dl><dt>Modelo de detección</dt><dd>No disponible</dd><dt>Modelo de clasificación</dt><dd>No disponible</dd><dt>Generación</dt><dd>{new Date(draft.createdAt).toLocaleString('es-PE')}</dd><dt>ID de sesión</dt><dd>{session.id}</dd></dl></section>
				{#if draft.status !== 'final'}
					<p class="report-edit" role="status">{dirty ? 'Cambios por guardar' : 'Cambios guardados'} · {captures.length !== draft.evidenceIds.length ? 'Faltan capturas vinculadas.' : !reviewComplete(draft) ? 'Revisa todas las capturas para marcar el informe como revisado.' : draft.status !== 'reviewed' ? 'Marca el informe como revisado para finalizarlo.' : 'Puedes finalizar el informe.'}</p><div class="actions report-edit">
						<button class:primary={dirty} disabled={saving || !dirty} onclick={() => draft && persist(draft)}>Guardar cambios</button>
						<button class:primary={!dirty && draft.status === 'draft' && reviewComplete(draft)} disabled={saving || draft.status === 'reviewed' || captures.length !== draft.evidenceIds.length || !reviewComplete(draft)} onclick={() => draft && persist(draft, 'reviewed')}>Marcar revisado</button>
						<button class:primary={draft.status === 'reviewed'} disabled={saving || draft.status !== 'reviewed' || dirty || captures.length !== draft.evidenceIds.length} onclick={() => (confirmFinal = true)}>Finalizar informe</button>
						{#if confirmFinal}
							<p>Al finalizar, se cerrará la edición de este informe.</p>
							<button class="primary" disabled={saving} onclick={() => draft && persist(draft, 'final')}>Confirmar finalización</button>
							<button onclick={() => (confirmFinal = false)}>Cancelar</button>
						{/if}
					</div>
				{/if}
			{/if}
			</div>
		{:else}
			<h2 id="report-title">Informe de colonoscopia</h2><p class="muted">Selecciona una sesión para ver su resumen.</p>
		{/if}
	</article>
	{/if}
</div>
<dialog class="finding-viewer" bind:this={viewer} aria-label="Captura de evidencia" onclose={() => (enlarged = null)}>
	<button onclick={() => viewer.close()}>Cerrar</button>
	{#if enlarged}<img src={evidenceImage(enlarged)} alt="Recorte de la región marcada por la IA" />{/if}
</dialog>

<dialog class="review-dialog" bind:this={editor} aria-labelledby="review-title" onclose={() => editing = null}>
 {#if editing}
  <header><div><h2 id="review-title">Revisar captura</h2><span>Captura {captures.findIndex(item => item.id === editing?.id) + 1}{#if editing.videoSeconds !== null} · {formatDuration(Math.floor(editing.videoSeconds))} en señal{/if}</span></div><button aria-label="Cerrar revisión" onclick={() => editor.close()}>×</button></header>
  <div class="capture-editor-body">
   <section><img src={evidenceImage(editing)} alt="Captura seleccionada para revisión"/><h3>Predicción de IA</h3><strong>{label(editing.label)}</strong><p>Clasificación {Math.round(editing.confidence * 100)} % · Detección {Math.round(editing.detectionConfidence * 100)} %</p></section>
   <section><h3>Revisión médica</h3><label>Decisión<select bind:value={decision}>{#each Object.entries(reviewLabels) as [key,text]}<option value={key}>{text}</option>{/each}</select></label><label>Observación de esta captura<textarea maxlength="1000" bind:value={note}></textarea></label></section>
  </div>
  <footer><button onclick={() => editor.close()}>Cancelar</button><button class="primary" onclick={() => {if(editing) validate(editing.id,{decision,note}); editor.close();}}>Aplicar al borrador</button></footer>
 {/if}
</dialog>
