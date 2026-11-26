<script lang="ts">
	import { resolve } from '$app/paths';
	import { env } from '$env/dynamic/public';
	import { usePreferences } from '$lib/preferences/context.svelte';
	import { useSessions } from '$lib/sessions/context.svelte';
	import { listEvidence, listFindings, listReports } from '$lib/sessions/evidence';
	import packageInfo from '../../../package.json';
	const preferences = usePreferences();
	const sessions = useSessions();
	let openSection = $state(-1);
	let service = $state<'idle' | 'checking' | 'connected' | 'disconnected' | 'error'>('idle');
	let exportFormat = $state('json');
	let message = $state('');
	let busy = $state(false);
	async function checkService() {
		service = 'checking';
		try {
			const url = (env.PUBLIC_API_URL || 'http://localhost:8000').replace(/\/$/, '');
			const response = await fetch(url + '/health', { cache: 'no-store', signal: AbortSignal.timeout(8000) });
			service = response.ok ? 'connected' : 'error';
		} catch {
			service = 'disconnected';
		}
	}
	async function exportData() {
		busy = true;
		message = '';
		try {
			const [evidence, findings, reports] = await Promise.all([listEvidence(), listFindings(), listReports()]);
			let content: string;
			let type: string;
			if (exportFormat === 'json') {
				content = JSON.stringify({ exportedAt: new Date().toISOString(), sessions: $state.snapshot(sessions.records), evidence, findings, reports }, null, 2);
				type = 'application/json';
			} else {
				const quote = (value: unknown) => {
					const raw = String(value ?? '');
					return '"' + (/^[=+@\-\t\r\n]/.test(raw) ? "'" : '') + raw.replaceAll('"', '""') + '"';
				};
				content = '\uFEFF' + [['Sesión', 'Fecha', 'Fuente', 'Estado', 'Inicio', 'Finalización'], ...sessions.records.map((item) => [item.id, item.createdAt, item.sourceType, item.status, item.startedAt, item.finishedAt])].map((row) => row.map(quote).join(';')).join('\r\n');
				type = 'text/csv;charset=utf-8';
			}
			const url = URL.createObjectURL(new Blob([content], { type }));
			const link = document.createElement('a');
			link.href = url;
			link.download = exportFormat === 'json' ? 'endosight-datos.json' : 'endosight-sesiones.csv';
			link.click();
			setTimeout(() => URL.revokeObjectURL(url), 1000);
			message = 'Archivo preparado para descarga.';
		} catch {
			message = 'No se pudieron leer los datos locales.';
		} finally {
			busy = false;
		}
	}
	const sections = [
		{ title: 'Visualización', description: 'Preferencias de pantalla y accesibilidad', icon: 'M3 4h18v13H3zM8 21h8m-4-4v4' },
		{ title: 'Señal y conexión', description: 'Fuente de video y conexión con el procesador', icon: 'M12 3v18M8 5a3 3 0 0 0-3 4 3 3 0 0 0 0 6 3 3 0 0 0 3 4m8-14a3 3 0 0 1 3 4 3 3 0 0 1 0 6 3 3 0 0 1-3 4' },
		{ title: 'Informes y exportación', description: 'Consulta y salida de informes de sesión', icon: 'M5 3h9l5 5v13H5zM14 3v5h5M8 13h8m-8 4h8' },
		{ title: 'Datos locales', description: 'Dónde se guardan las sesiones y evidencias', icon: 'M4 6c0-2 16-2 16 0v12c0 2-16 2-16 0zM4 6c0 2 16 2 16 0M4 12c0 2 16 2 16 0' },
		{ title: 'Acerca de EndoSight', description: 'Uso previsto y alcance experimental', icon: 'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18ZM12 10v6m0-9v.1' }
	];
</script>
<svelte:head><title>Configuración · EndoSight</title></svelte:head>
<div class="support-page settings-page">
	<header class="support-page-header"><p class="support-kicker">ESTACIÓN DE TRABAJO</p><h1>Configuración</h1><p>Consulta las opciones de tu entorno de trabajo.</p></header>
	<div class="settings-list">
		{#each sections as section, index (section.title)}
			<details open={openSection === index} ontoggle={(event) => { if (event.currentTarget.open) openSection = index; else if (openSection === index) openSection = -1; }}>
				<summary><span class="support-topic-icon"><svg viewBox="0 0 24 24" aria-hidden="true"><path d={section.icon}/></svg></span><span><strong>{section.title}</strong><small>{section.description}</small></span><svg class="settings-chevron" viewBox="0 0 24 24" aria-hidden="true"><path d="m9 5 7 7-7 7"/></svg></summary>
				<div class="settings-content">
					{#if index === 0}
						<label>Vista inicial del video
							<select value={preferences.value.defaultVideo} disabled={!preferences.ready} onchange={(event) => preferences.update('defaultVideo', event.currentTarget.value as 'annotated' | 'original')}>
								<option value="annotated">Video con anotaciones</option><option value="original">Video original</option>
							</select>
						</label>
						<p class="hint">Puedes alternar las vistas durante la sesión.</p>
						<p class="hint">Las etiquetas, la confianza, el color y el grosor se dibujan en el video del servidor y no se pueden cambiar desde esta interfaz.</p>
						<a class="text-link" href={resolve('/accessibility')}>Opciones de accesibilidad →</a>
					{:else if index === 1}
						<div class="settings-actions"><button onclick={checkService} disabled={service === 'checking'}>Comprobar servicio</button><span role="status">{service === 'idle' ? 'Sin comprobar' : service === 'checking' ? 'Comprobando…' : service === 'connected' ? 'Servicio disponible' : service === 'error' ? 'Error del servicio' : 'Sin conexión'}</span></div>
						<p class="hint">La comprobación verifica el servicio HTTP. La conexión de video se comprueba al iniciar la asistencia.</p>
						<a class="text-link" href={resolve('/models')}>Consultar modelos de IA →</a>
						<label class="settings-toggle"><input type="checkbox" checked={preferences.value.showProcessingStatus} disabled={!preferences.ready} onchange={(event) => preferences.update('showProcessingStatus', event.currentTarget.checked)} /> Mostrar estado del procesamiento</label>
						<p class="hint">EndoSight es una herramienta experimental de apoyo visual. Sus anotaciones no sustituyen la evaluación del especialista.</p>
						<div class="settings-actions"><a class="button" href={resolve('/sessions/new')}>Preparar fuente</a><a class="button" href={resolve('/webrtc-test')}>Diagnóstico de conexión</a></div>
					{:else if index === 2}
						<p>La salida disponible es PDF mediante el diálogo de impresión del navegador. Word y la selección de apartados requieren desarrollo adicional.</p><a class="text-link" href={resolve('/reports')}>Ir a informes →</a>
					{:else if index === 3}
						<p>Las sesiones se guardan en almacenamiento local y las capturas, revisiones e informes en IndexedDB de este navegador.</p>
						<label>Exportar datos
							<select bind:value={exportFormat}><option value="json">JSON · todos los registros y capturas</option><option value="csv">CSV · sesiones</option></select>
						</label>
						<button onclick={exportData} disabled={busy}>{busy ? 'Preparando…' : 'Descargar datos'}</button>
						<p role="status" class="hint">{message}</p>
						<p class="hint">La eliminación selectiva aún no está disponible.</p>
					{:else}
						<strong>EndoSight · Plataforma experimental de asistencia endoscópica</strong>
						<dl class="settings-metadata"><dt>Versión</dt><dd>{packageInfo.version}</dd><dt>Plataforma</dt><dd>Aplicación web</dd><dt>Finalidad</dt><dd>Investigación</dd></dl>
						<p>EndoSight es una herramienta de investigación diseñada para apoyar la visualización de video endoscópico mediante inteligencia artificial. No proporciona diagnósticos autónomos.</p>
					{/if}
				</div>
			</details>
		{/each}
	</div>
</div>
