<script lang="ts">
	import { resolve } from '$app/paths';
	import { usePreferences } from '$lib/preferences/context.svelte';
	import { createClientId } from '$lib/utils/client-id';
	import { parseDetection, saveEvidence, evidenceImage, type Evidence } from '$lib/sessions/evidence';
	import { onDestroy } from 'svelte';
	import { goto, beforeNavigate } from '$app/navigation';
	import { env } from '$env/dynamic/public';
	import { fetchIceServers, turnConnectivityError } from '$lib/webrtc/ice';
	import { useSessions } from '$lib/sessions/context.svelte';
	import { formatDuration, durationSeconds } from '$lib/domain/sessions/session';
	let { preparing, sessionId }: { preparing: boolean; sessionId: string } = $props();
	let signalPanel = $state<HTMLElement>(undefined!);
	let sourceControls = $state<HTMLButtonElement>(undefined!);

	async function focusSignalSettings() {
		if (document.fullscreenElement === signalPanel) await toggleFullscreen();
		sourceControls.focus();
	}

	async function toggleFullscreen() {
		try {
			if (document.fullscreenElement === signalPanel) await document.exitFullscreen();
			else await signalPanel.requestFullscreen();
		} catch {
			errorMessage = 'No se pudo abrir la vista en pantalla completa.';
		}
	}
	const sessions = useSessions();
	const preferences = usePreferences();
	const apiUrl = (env.PUBLIC_API_URL || 'http://localhost:8000').replace(/\/$/, '');
	let sourceType = $state<'camera' | 'file'>('camera');
	let selectedCameraId = $state('');
	let selectedFile = $state<File | null>(null);
	let cameras = $state<MediaDeviceInfo[]>([]);
	let ready = $state(false);
	let busy = $state(false);
	let connected = $state(false);
	let connecting = $state(false);
	let status = $state('Selecciona una fuente para preparar la sesión.');
	let errorMessage = $state('');
	let resolution = $state('—');
	let iceState = $state('new');
	let annotated = $state(true);
	let elapsed = $state(0);
	let recordId = $state('');
	let recentEvidence = $state<Evidence[]>([]);
	let evidenceCount = $state(0);
	let evidenceError = $state('');
	let activeId = $derived(recordId || sessionId);
	let record = $derived(sessions.find(activeId));
	let localVideo = $state<HTMLVideoElement>(undefined!);
	let remoteVideo = $state<HTMLVideoElement>(undefined!);
	let fileVideo: HTMLVideoElement;
	let canvas: HTMLCanvasElement;
	let localStream: MediaStream | null = null;
	let peer: RTCPeerConnection | null = null;
	let fileUrl: string | null = null;
	let frameId: number | null = null;
	let timer: ReturnType<typeof setInterval> | null = null;
	let request: AbortController | null = null;
	let generation = 0;
	let destroyed = false;
	let allowLeave = false;

	function current(token: number) {
		return !destroyed && token === generation;
	}
	function stopPeer() {
		request?.abort();
		request = null;
		const previous = peer;
		peer = null;
		previous?.close();
		if (remoteVideo) {
			remoteVideo.pause();
			remoteVideo.srcObject = null;
		}
		connected = false;
		connecting = false;
		iceState = 'closed';
	}
	function releaseSource() {
		generation += 1;
		stopPeer();
		if (frameId !== null) cancelAnimationFrame(frameId);
		frameId = null;
		localStream?.getTracks().forEach((track) => track.stop());
		localStream = null;
		if (localVideo) {
			localVideo.pause();
			localVideo.srcObject = null;
		}
		if (fileVideo) {
			fileVideo.pause();
			fileVideo.removeAttribute('src');
			fileVideo.load();
		}
		if (fileUrl) URL.revokeObjectURL(fileUrl);
		fileUrl = null;
		ready = false;
		resolution = '—';
	}
	async function loadCameras() {
		try {
			if (!navigator.mediaDevices?.enumerateDevices)
				throw new Error('El navegador no ofrece acceso a dispositivos. Usa localhost o HTTPS.');
			cameras = (await navigator.mediaDevices.enumerateDevices()).filter(
				(device) => device.kind === 'videoinput'
			);
		} catch (error) {
			errorMessage =
				error instanceof Error ? error.message : 'No se pudieron consultar los dispositivos.';
		}
	}
	function changeSource() {
		releaseSource();
		status = 'Prepara de nuevo la fuente seleccionada.';
		errorMessage = '';
	}
	async function preview() {
		if (busy) return;
		releaseSource();
		const token = generation;
		busy = true;
		errorMessage = '';
		status = 'Preparando fuente...';
		try {
			if (sourceType === 'camera') {
				if (!navigator.mediaDevices?.getUserMedia)
					throw new Error('Se requiere acceso a cámara en localhost o HTTPS.');
				const stream = await navigator.mediaDevices.getUserMedia({
					video: {
						width: { ideal: 768 },
						height: { ideal: 576 },
						frameRate: { ideal: 24 },
						...(selectedCameraId ? { deviceId: { exact: selectedCameraId } } : {})
					},
					audio: false
				});
				if (!current(token)) {
					stream.getTracks().forEach((track) => track.stop());
					return;
				}
				localStream = stream;
				localVideo.srcObject = stream;
				await localVideo.play();
				if (!current(token)) return;
				const track = stream.getVideoTracks()[0];
				const settings = track.getSettings();
				resolution = `${settings.width ?? '—'} × ${settings.height ?? '—'}`;
				track.onended = () => {
					if (localStream !== stream || destroyed) return;
					releaseSource();
					status = 'Fuente desconectada';
					errorMessage =
						'La fuente dejó de transmitir. Finaliza la sesión y vuelve a preparar el dispositivo.';
				};
				await loadCameras();
			} else {
				if (!selectedFile) throw new Error('Selecciona un archivo de video.');
				fileUrl = URL.createObjectURL(selectedFile);
				fileVideo.muted = true;
				fileVideo.loop = true;
				await new Promise<void>((resolve, reject) => {
					const timeout = setTimeout(() => {
						cleanup();
						reject(new Error('El archivo no respondió en 10 segundos.'));
					}, 10000);
					function cleanup() {
						clearTimeout(timeout);
						fileVideo.onloadedmetadata = null;
						fileVideo.onerror = null;
					}
					fileVideo.onloadedmetadata = () => {
						cleanup();
						resolve();
					};
					fileVideo.onerror = () => {
						cleanup();
						reject(new Error('No se pudo leer el archivo de video.'));
					};
					fileVideo.src = fileUrl!;
				});
				if (!current(token)) return;
				canvas.width = fileVideo.videoWidth;
				canvas.height = fileVideo.videoHeight;
				if (!canvas.width || !canvas.height) throw new Error('Dimensiones de video inválidas.');
				const context = canvas.getContext('2d');
				if (!context || !canvas.captureStream)
					throw new Error('El navegador no admite la captura de este video.');
				await fileVideo.play();
				if (!current(token)) return;
				context.drawImage(fileVideo, 0, 0, canvas.width, canvas.height);
				localStream = canvas.captureStream(24);
				localVideo.srcObject = localStream;
				await localVideo.play();
				if (!current(token)) return;
				resolution = `${canvas.width} × ${canvas.height}`;
				const draw = () => {
					if (!current(token) || fileVideo.paused) return;
					context.drawImage(fileVideo, 0, 0, canvas.width, canvas.height);
					frameId = requestAnimationFrame(draw);
				};
				draw();
			}
			if (!current(token)) return;
			ready = true;
			status = 'Fuente lista. Puedes iniciar la asistencia.';
		} catch (error) {
			if (!current(token)) return;
			releaseSource();
			status = 'No se pudo preparar la fuente';
			errorMessage = error instanceof Error ? error.message : 'Error al preparar el video.';
		} finally {
			if (!destroyed) busy = false;
		}
	}
	async function waitForIce(pc: RTCPeerConnection, signal: AbortSignal) {
		if (pc.iceGatheringState === 'complete') return;
		await new Promise<void>((resolve, reject) => {
			const timeout = setTimeout(() => {
				cleanup();
				reject(new Error('Tiempo de espera ICE agotado.'));
			}, 10000);
			function cleanup() {
				clearTimeout(timeout);
				pc.removeEventListener('icegatheringstatechange', check);
				signal.removeEventListener('abort', abort);
			}
			function check() {
				if (pc.iceGatheringState === 'complete') {
					cleanup();
					resolve();
				}
			}
			function abort() {
				cleanup();
				reject(new Error('Conexión cancelada.'));
			}
			pc.addEventListener('icegatheringstatechange', check);
			signal.addEventListener('abort', abort);
			if (signal.aborted) abort();
			else check();
		});
	}
	async function startAssistance() {
		if (!ready || !localStream || connecting || connected) return;
		errorMessage = '';
		if (!recordId) recordId = sessions.create(sourceType).id;
		stopPeer();
		let pendingPeer: RTCPeerConnection | null = null;
		const controller = new AbortController();
		request = controller;
		connecting = true;
		status = 'Negociando conexión con FastAPI...';
		const timeout = setTimeout(() => controller.abort(), 60000);
		const valid = () => !destroyed && peer === pendingPeer && !controller.signal.aborted;
		try {
			const iceServers = await fetchIceServers(apiUrl, controller.signal);
			if (destroyed || controller.signal.aborted || request !== controller) return;
			const pc = new RTCPeerConnection({ iceServers });
			pendingPeer = pc;
			peer = pc;
			const evidenceSession = recordId;
			const evidenceChannel = pc.createDataChannel('detection-evidence');
			evidenceChannel.onmessage = async (event) => {
				if (!valid()) return;
				const detection = parseDetection(event.data);
				if (!detection) return;
				const item = { ...detection, id: createClientId(), sessionId: evidenceSession };
				try {
					await saveEvidence(item);
					if (destroyed) return;
					recentEvidence = [item, ...recentEvidence].slice(0, 6);
					evidenceCount += 1;
				} catch {
					evidenceError = 'No se pudo guardar una evidencia en este navegador.';
				}
			};
			pc.addEventListener('icecandidateerror', () => {
				if (peer === pc && !destroyed) errorMessage = turnConnectivityError;
			});
			if (preparing) await goto(resolve('/sessions/[id]/live', { id: recordId }));
			if (!valid()) return;
			pc.onconnectionstatechange = () => {
				if (peer !== pc || destroyed) return;
				connected = pc.connectionState === 'connected';
				status = `WebRTC: ${pc.connectionState}`;
				if (connected && sessions.find(recordId)?.status !== 'finished') {
					sessions.start(recordId);
					if (!timer)
						timer = setInterval(() => {
							const item = sessions.find(recordId);
							if (item) elapsed = durationSeconds(item);
						}, 1000);
				}
				if (pc.connectionState === 'failed' || pc.connectionState === 'disconnected') {
					errorMessage =
						'La conexión se interrumpió. La imagen anotada podría estar detenida; consulta la fuente original.';
					annotated = false;
				}
				if (connected) errorMessage = '';
			};
			pc.oniceconnectionstatechange = () => {
				if (peer === pc) iceState = pc.iceConnectionState;
			};
			pc.ontrack = (event) => {
				if (!valid() || event.track.kind !== 'video') return;
				remoteVideo.srcObject = event.streams[0] ?? new MediaStream([event.track]);
				remoteVideo.play().catch(() => {
					if (peer === pc) errorMessage = 'El navegador no pudo reproducir el video procesado.';
				});
			};
			for (const track of localStream.getTracks()) pc.addTrack(track, localStream);
			const offer = await pc.createOffer();
			if (!valid()) return;
			await pc.setLocalDescription(offer);
			if (!valid()) return;
			await waitForIce(pc, controller.signal);
			if (!valid()) return;
			if (!pc.localDescription) throw new Error('No se pudo generar la oferta SDP.');
			const response = await fetch(`${apiUrl}/webrtc/offer`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ sdp: pc.localDescription.sdp, type: pc.localDescription.type }),
				signal: controller.signal
			});
			if (!response.ok)
				throw new Error(
					`Error de señalización HTTP ${response.status}. Comprueba la API y los modelos.`
				);
			const answer = await response.json();
			if (!valid()) return;
			await pc.setRemoteDescription(new RTCSessionDescription(answer));
			if (!valid()) return;
			annotated = preferences.value.defaultVideo === 'annotated';
			status = `WebRTC: ${pc.connectionState}`;
		} catch (error) {
			if (request !== controller || destroyed) return;
			const aborted = controller.signal.aborted;
			stopPeer();
			annotated = false;
			status = 'Asistencia no disponible';
			errorMessage = aborted
				? 'Conexión cancelada o tiempo de espera agotado. Puedes reintentar.'
				: error instanceof Error
					? error.message
					: 'No se pudo conectar con FastAPI.';
		} finally {
			clearTimeout(timeout);
			if (request === controller) {
				connecting = false;
				request = null;
			}
		}
	}
	function pauseAssistance() {
		stopPeer();
		annotated = false;
		status = 'Asistencia detenida. La fuente original continúa disponible.';
	}
	async function finish() {
		if (timer) clearInterval(timer);
		timer = null;
		const id = activeId;
		if (id) sessions.finish(id);
		releaseSource();
		allowLeave = true;
		await goto(id ? resolve('/sessions/[id]', { id }) : resolve('/sessions'));
	}
	beforeNavigate((navigation) => {
		if (allowLeave || destroyed) return;
		const target = navigation.to?.url.pathname;
		if (target === `/sessions/${recordId}/live` && preparing) return;
		if (!ready && !connecting && !recordId) return;
		if (navigation.type === 'leave') {
			navigation.cancel();
			return;
		}
		if (
			!window.confirm(
				'¿Salir y cerrar la fuente de video? Se finalizará la sesión activa. No se guarda video.'
			)
		) {
			navigation.cancel();
			return;
		}
		if (activeId) sessions.finish(activeId);
		releaseSource();
		allowLeave = true;
	});
	onDestroy(() => {
		destroyed = true;
		if (timer) clearInterval(timer);
		if (activeId) sessions.finish(activeId);
		if (typeof window !== 'undefined') releaseSource();
	});
</script>

<section class="procedure-workspace" class:signal-setup={preparing} class:live-workspace={!preparing}>
	{#if !preparing && !record}
		<section class="empty-state">
			<h1>Sesión no disponible</h1>
			<p class="muted">Prepara una nueva sesión para conectar el video.</p>
			<a class="button primary" href={resolve('/sessions/new')}>Nueva sesión</a>
		</section>
	{:else}
		<header class="workspace-heading">
			{#if preparing}
				<h1 class="visually-hidden">Verificar señal de video</h1>
				<a class="text-link" href={resolve('/sessions')}>← Sesiones</a>
			{:else}
				<div class="live-breadcrumb"><a class="text-link" href={resolve('/sessions')}>← Sesiones</a><span aria-hidden="true">/</span><h1>Asistencia en curso</h1></div>
			{/if}
			{#if !preparing}<div class="session-indicators">
					<span class="connection-label" class:positive={connected}
						>{connected ? 'Conectado' : connecting ? 'Conectando' : 'Sin conexión'}</span
					><span class="session-time" aria-label="Tiempo de sesión"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></svg>{formatDuration(elapsed)}</span>
				</div>{/if}
		</header>
		<div class="procedure-grid">
			<section class="video-panel" aria-label="Visualización de video" bind:this={signalPanel}>
				<div class="video-heading">
					<h2>
						{preparing
							? 'Señal de video'
							: annotated && connected
								? 'Video con anotaciones'
								: 'Video original'}
					</h2>
					<span>{resolution}</span>
						<div class="signal-view-tools">
							<button aria-label="Alternar pantalla completa" onclick={toggleFullscreen}><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 4H4v5m11-5h5v5M4 15v5h5m11-5v5h-5" /></svg></button>
							{#if preparing}
							<button aria-label="Ir a configuración de señal" onclick={focusSignalSettings}><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3l2 2 3-.2.8 2.8L20 9l-1 3 1 3-2.2 1.4-.8 2.8-3-.2-2 2-2-2-3 .2-.8-2.8L4 15l1-3-1-3 2.2-1.4L7 4.8l3 .2z" /><circle cx="12" cy="12" r="3" /></svg></button>
							{/if}
						</div>
				</div>
				<div class="video-stage">
					<video
						bind:this={localVideo}
						autoplay
						muted
						playsinline
						class:hidden-video={!preparing && annotated && connected}
						aria-label="Fuente de video original"
					></video>
					<video
						bind:this={remoteVideo}
						autoplay
						muted
						playsinline
						class:hidden-video={preparing || !annotated || !connected}
						aria-label="Video procesado con anotaciones de IA"
					></video>
					{#if !ready}<div class="video-empty">
							{#if preparing}<svg class="signal-monitor" viewBox="0 0 64 56" aria-hidden="true"><rect x="3" y="3" width="58" height="39" rx="5" /><path d="m27 14 15 9-15 9zM32 42v9m-12 0h24" /></svg>{/if}
							<strong>Sin señal</strong><small
								>{preparing
									? 'Selecciona una fuente y pulsa Previsualizar.'
									: 'La fuente dejó de transmitir.'}</small
							>
							{#if preparing}<button class="signal-preview" onclick={preview} disabled={busy || (sourceType === 'file' && !selectedFile)}>{busy ? 'Preparando…' : '▷ Previsualizar'}</button>{/if}
						</div>{/if}
				</div>
			</section>
			<aside
				class="control-panel"
				aria-label={preparing ? 'Preparación de fuente' : 'Controles de sesión'}
			>
				<div class="control-content">
					{#if preparing}
						<h2 class="home-card-title"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 6h16M4 12h16M4 18h16M8 3v6m8 0v6m-6 0v6" /></svg>Configuración de señal</h2>
						<div class="source-switch" role="group" aria-label="Tipo de fuente">
							<button
								bind:this={sourceControls}
								aria-pressed={sourceType === 'camera'}
								disabled={busy}
								onclick={() => {
									changeSource();
									sourceType = 'camera';
								}}><svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="2" /><path d="M7 10h4m-2-2v4m5 3h3" /></svg>Capturadora</button
							><button
								aria-pressed={sourceType === 'file'}
								disabled={busy}
								onclick={() => {
									changeSource();
									sourceType = 'file';
								}}><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 6h7l2 3h9v10H3zM3 12h18" /></svg>Archivo</button
							>
						</div>
						{#if sourceType === 'camera'}
							<label for="camera">Dispositivo</label><select
								id="camera"
								bind:value={selectedCameraId}
								onchange={changeSource}
								disabled={busy}
								><option value="">Dispositivo predeterminado</option
								>{#each cameras as camera (camera.deviceId)}<option value={camera.deviceId}
										>{camera.label || 'Dispositivo de video'}</option
									>{/each}</select
							>
							<button class="text-button" onclick={loadCameras} disabled={busy}
								>Actualizar dispositivos</button
							>
						{:else}
							<label for="file">Archivo de video</label><input
								id="file"
								type="file"
								accept="video/*"
								disabled={busy}
								onchange={(event) => {
									changeSource();
									selectedFile = event.currentTarget.files?.[0] ?? null;
								}}
							/>
							<p class="hint">Se reproducirá en bucle.</p>
						{/if}
					{:else}
						<section class="live-controls">
						<h2 class="home-card-title"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 6h18M3 12h18M3 18h18M8 3v6m8 0v6m-6 0v6" /></svg>Controles</h2>
						<div class="session-control-buttons">
							<button
								onclick={() => (annotated = !annotated)}
								disabled={!connected}
								aria-pressed={!annotated}
								>{annotated ? 'Mostrar original' : 'Mostrar anotaciones'}</button
							>{#if connected || connecting}<button class="primary" onclick={pauseAssistance}
									>{connecting ? 'Cancelar conexión' : 'Detener asistencia'}</button
								>{:else}<button class="primary" onclick={startAssistance} disabled={!ready}
									>Reintentar asistencia</button
								>{/if}
						</div>
						</section>
						<section class="events-placeholder">
							<h2 class="home-card-title"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9" /><circle cx="12" cy="12" r="5" /></svg>Eventos</h2>
							<p class="muted">{evidenceCount} evidencias guardadas</p>
							{#if evidenceError}<p role="alert">{evidenceError}</p>{/if}
							<ul class="live-evidence">
								{#each recentEvidence as item (item.id)}
									<li><img src={evidenceImage(item)} alt="" /><span><strong>{item.label}</strong><small>{new Date(item.capturedAt).toLocaleTimeString('es-PE')} · {Math.round(item.confidence * 100)} %</small></span></li>
								{/each}
							</ul>
						</section>
						<details class="technical-details">
							<summary>Conexión</summary>
							<dl class="technical">
								<dt>Resolución</dt>
								<dd>{resolution}</dd>
								<dt>ICE</dt>
								<dd>{iceState}</dd>
							</dl>
						</details>
					{/if}
					<div class="workspace-status">
						{#if preparing || preferences.value.showProcessingStatus || connecting || !connected}
							<p class="connection-status" role="status">{status}</p>
						{/if}
						{#if errorMessage}<p class="error" role="alert">{errorMessage}</p>{/if}
					</div>
				</div>
				<div class="control-actions">
					{#if preparing}
						<button onclick={preview} disabled={busy || (sourceType === 'file' && !selectedFile)}
							>{busy
								? 'Preparando...'
								: ready
									? 'Actualizar vista previa'
									: 'Previsualizar'}</button
						>
						<button
							class="primary"
							onclick={startAssistance}
							disabled={!ready || busy || connecting}>Iniciar asistencia</button
						>
						<a class="cancel-link" href={resolve('/sessions')}>Cancelar</a>
					{:else}<button class="danger" onclick={finish}>Finalizar sesión</button>{/if}
				</div>
			</aside>
		</div>
	{/if}
</section>
<video bind:this={fileVideo} muted playsinline preload="auto" class="file-source" aria-hidden="true"
></video>
<canvas bind:this={canvas} class="auxiliary"></canvas>
