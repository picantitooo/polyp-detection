
	<script lang="ts">
	import { onDestroy } from 'svelte';

	type SourceType = 'camera' | 'file';

	const API_URL = 'http://localhost:8000';

	let sourceType = $state<SourceType>('camera');
	let selectedFile = $state<File | null>(null);
	let selectedCameraId = $state('');
	let cameras = $state<MediaDeviceInfo[]>([]);

	let status = $state('Desconectado');
	let iceState = $state('new');
	let isConnecting = $state(false);
	let isConnected = $state(false);
	let isStreaming = $state(false);
	let errorMessage = $state('');

	let elapsedSeconds = $state(0);
	let inputResolution = $state('—');

	let localVideo: HTMLVideoElement;
	let remoteVideo: HTMLVideoElement;
	let fileVideo: HTMLVideoElement;
	let captureCanvas: HTMLCanvasElement;

	let peerConnection: RTCPeerConnection | null = null;
	let localStream: MediaStream | null = null;
	let fileObjectUrl: string | null = null;

	let captureContext: CanvasRenderingContext2D | null = null;
	let captureAnimationFrame: number | null = null;
	let sessionTimer: ReturnType<typeof setInterval> | null = null;

	async function loadCameras() {
		try {
		const devices = await navigator.mediaDevices.enumerateDevices();

		cameras = devices.filter(
			(device) => device.kind === 'videoinput'
		);
		} catch (error) {
		console.error('Error consultando cámaras:', error);
		}
	}

	function formatDuration(seconds: number): string {
		const minutes = Math.floor(seconds / 60);
		const remainingSeconds = seconds % 60;

		return `${String(minutes).padStart(2, '0')}:${String(
		remainingSeconds
		).padStart(2, '0')}`;
	}

	function handleFileChange(event: Event) {
		const input = event.currentTarget as HTMLInputElement;
		const file = input.files?.[0] ?? null;

		selectedFile = file;
	}

	async function waitForIceGathering(
		pc: RTCPeerConnection
	): Promise<void> {
		if (pc.iceGatheringState === 'complete') return;

		await new Promise<void>((resolve, reject) => {
		const timeout = setTimeout(() => {
			pc.removeEventListener('icegatheringstatechange', check);
			reject(new Error('Tiempo de espera ICE agotado.'));
		}, 10000);

		function check() {
			if (pc.iceGatheringState === 'complete') {
			clearTimeout(timeout);
			pc.removeEventListener('icegatheringstatechange', check);
			resolve();
			}
		}

		pc.addEventListener('icegatheringstatechange', check);
		check();
		});
	}

	async function prepareCamera(): Promise<MediaStream> {
		const videoConstraints: MediaTrackConstraints = {
		width: { ideal: 768 },
		height: { ideal: 576 },
		frameRate: { ideal: 24 }
		};

		if (selectedCameraId) {
		videoConstraints.deviceId = {
			exact: selectedCameraId
		};
		}

		const stream = await navigator.mediaDevices.getUserMedia({
		video: videoConstraints,
		audio: false
		});

		localVideo.srcObject = stream;
		console.log('[Video] Iniciando vista previa local...');

		await localVideo.play();

		console.log('[Video] Vista previa local iniciada');

		const track = stream.getVideoTracks()[0];
		const settings = track.getSettings();

		inputResolution =
		`${settings.width ?? '—'} × ${settings.height ?? '—'}`;

		await loadCameras();

		return stream;
	}

	async function prepareVideoFile(): Promise<MediaStream> {
		if (!selectedFile) {
		throw new Error('Selecciona un archivo de video.');
		}

		fileObjectUrl = URL.createObjectURL(selectedFile);

		fileVideo.src = fileObjectUrl;
		fileVideo.muted = true;
		fileVideo.loop = true;
		fileVideo.playsInline = true;

		await new Promise<void>((resolve, reject) => {
		fileVideo.onloadedmetadata = () => resolve();
		fileVideo.onerror = () =>
			reject(new Error('No se pudo cargar el archivo de video.'));
		});

		const width = fileVideo.videoWidth;
		const height = fileVideo.videoHeight;

		if (!width || !height) {
		throw new Error('El video no tiene dimensiones válidas.');
		}

		captureCanvas.width = width;
		captureCanvas.height = height;

		captureContext = captureCanvas.getContext('2d');

		if (!captureContext) {
		throw new Error('No se pudo inicializar el canvas.');
		}

		inputResolution = `${width} × ${height}`;

		console.log('[Video] Iniciando reproducción...');

		await Promise.race([
		fileVideo.play(),

		new Promise<never>((_, reject) => {
			setTimeout(() => {
			reject(
				new Error(
				'El video no comenzó a reproducirse en 10 segundos.'
				)
			);
			}, 10000);
		})
		]);

		console.log('[Video] Reproducción iniciada correctamente');

		// Inicializar el primer fotograma antes de capturar.
		captureContext.drawImage(fileVideo, 0, 0, width, height);

		const stream = captureCanvas.captureStream(24);

		// Mostrar en la vista local exactamente el flujo enviado.
		localVideo.srcObject = stream;
		await localVideo.play();

		function drawFrame() {
		if (!captureContext || fileVideo.paused) return;

		captureContext.drawImage(
			fileVideo,
			0,
			0,
			captureCanvas.width,
			captureCanvas.height
		);

		captureAnimationFrame = requestAnimationFrame(drawFrame);
		}

		drawFrame();

		return stream;
	}

	async function startSession() {
		if (isConnecting || isStreaming) return;

		isConnecting = true;
		errorMessage = '';
		status = 'Preparando fuente de video...';

		try {
		if (sourceType === 'camera') {
			localStream = await prepareCamera();
		} else {
			localStream = await prepareVideoFile();
		}

		const pc = new RTCPeerConnection({
			iceServers: []
		});

		peerConnection = pc;
		isStreaming = true;

		pc.onconnectionstatechange = () => {
			if (peerConnection !== pc) return;

			status = `WebRTC: ${pc.connectionState}`;
			isConnected = pc.connectionState === 'connected';

			if (pc.connectionState === 'failed') {
			errorMessage = 'La conexión WebRTC falló.';
			}
		};

		pc.oniceconnectionstatechange = () => {
			if (peerConnection === pc) {
			iceState = pc.iceConnectionState;
			}
		};

		pc.ontrack = (event) => {
			if (
			peerConnection !== pc ||
			event.track.kind !== 'video'
			) {
			return;
			}

			remoteVideo.srcObject =
			event.streams[0] ??
			new MediaStream([event.track]);

			remoteVideo.play().catch(console.error);
		};

		for (const track of localStream.getTracks()) {
			pc.addTrack(track, localStream);
		}

		status = 'Negociando conexión...';

		const offer = await pc.createOffer();
		await pc.setLocalDescription(offer);
		await waitForIceGathering(pc);

		if (!pc.localDescription) {
			throw new Error('No se pudo generar la oferta SDP.');
		}

		const response = await fetch(`${API_URL}/webrtc/offer`, {
			method: 'POST',
			headers: {
			'Content-Type': 'application/json'
			},
			body: JSON.stringify({
			sdp: pc.localDescription.sdp,
			type: pc.localDescription.type
			})
		});

		if (!response.ok) {
			throw new Error(
			`Error de señalización: HTTP ${response.status}`
			);
		}

		const answer = await response.json();

		if (peerConnection !== pc) return;

		await pc.setRemoteDescription(
			new RTCSessionDescription(answer)
		);

		if (pc.connectionState !== 'connected') {
			status = `WebRTC: ${pc.connectionState}`;
		}

		elapsedSeconds = 0;

		sessionTimer = setInterval(() => {
			elapsedSeconds += 1;
		}, 1000);
		} catch (error) {
		const message =
			error instanceof Error
			? error.message
			: 'Error desconocido.';

		stopSession();
		errorMessage = message;
		} finally {
		isConnecting = false;
		}
	}

	function stopSession() {
		if (sessionTimer !== null) {
		clearInterval(sessionTimer);
		sessionTimer = null;
		}

		if (captureAnimationFrame !== null) {
		cancelAnimationFrame(captureAnimationFrame);
		captureAnimationFrame = null;
		}

		if (peerConnection) {
		peerConnection.close();
		peerConnection = null;
		}

		if (localStream) {
		for (const track of localStream.getTracks()) {
			track.stop();
		}
		localStream = null;
		}

		if (localVideo) {
		localVideo.pause();
		localVideo.srcObject = null;
		}

		if (remoteVideo) {
		remoteVideo.pause();
		remoteVideo.srcObject = null;
		}

		if (fileVideo) {
		fileVideo.pause();
		fileVideo.removeAttribute('src');
		fileVideo.load();
		}

		if (fileObjectUrl) {
		URL.revokeObjectURL(fileObjectUrl);
		fileObjectUrl = null;
		}

		captureContext = null;

		isConnected = false;
		isStreaming = false;
		isConnecting = false;

		status = 'Desconectado';
		iceState = 'closed';
		elapsedSeconds = 0;
		inputResolution = '—';
	}

	onDestroy(() => {
		stopSession();
	});
	</script>

	<svelte:head>
	<title>Detección de pólipos</title>
	<meta
		name="description"
		content="Prototipo experimental de detección y clasificación de pólipos mediante inteligencia artificial."
	/>
	</svelte:head>

	<div class="min-h-screen bg-white text-slate-900">
	<header class="border-b border-slate-200 bg-white">
		<div class="mx-auto flex max-w-7xl items-center justify-between px-6 py-5">
		<div>
			<h1 class="text-2xl font-bold tracking-tight">
			Detección de Pólipos Colorrectales
			</h1>
			<p class="mt-1 text-sm text-slate-500">
			Detección y clasificación asistida por IA
			</p>
		</div>

		<span
			class="rounded-full border px-3 py-1 text-xs font-semibold"
			class:border-emerald-200={isConnected}
			class:bg-emerald-50={isConnected}
			class:text-emerald-700={isConnected}
			class:border-slate-200={!isConnected}
			class:bg-slate-50={!isConnected}
			class:text-slate-700={!isConnected}
		>
			{isConnected ? 'Conectado' : 'Sin conexión'}
		</span>
		</div>
	</header>

	<main class="mx-auto max-w-7xl space-y-6 px-6 py-8">
		<section class="rounded-2xl border border-slate-200 bg-white shadow-sm p-6">
		<div class="mb-5">
			<h2 class="text-lg font-semibold">
			Configuración de la fuente
			</h2>
			<p class="mt-1 text-sm text-slate-500">
			Selecciona una cámara o carga un video de colonoscopia.
			</p>
		</div>

		<div class="mb-5 flex flex-wrap gap-3">
			<button
			onclick={() => (sourceType = 'camera')}
			disabled={isStreaming || isConnecting}
			class="rounded-lg border px-5 py-2.5 text-sm font-medium disabled:opacity-50"
			class:border-blue-600={sourceType === 'camera'}
			class:bg-blue-600={sourceType === 'camera'}
			class:text-white={sourceType === 'camera'}
			class:border-slate-200={sourceType !== 'camera'}
			class:bg-slate-50={sourceType !== 'camera'}
			>
			Cámara
			</button>

			<button
			onclick={() => (sourceType = 'file')}
			disabled={isStreaming || isConnecting}
			class="rounded-lg border px-5 py-2.5 text-sm font-medium disabled:opacity-50"
			class:border-blue-600={sourceType === 'file'}
			class:bg-blue-600={sourceType === 'file'}
			class:text-white={sourceType === 'file'}
			class:border-slate-200={sourceType !== 'file'}
			class:bg-slate-50={sourceType !== 'file'}
			>
			Archivo de video
			</button>
		</div>

		{#if sourceType === 'camera'}
			<div class="max-w-xl">
			<label
				for="camera-select"
				class="mb-2 block text-sm font-medium text-slate-700"
			>
				Dispositivo de captura
			</label>

			<select
				id="camera-select"
				bind:value={selectedCameraId}
				disabled={isStreaming || isConnecting}
				onclick={loadCameras}
				class="w-full rounded-lg border border-slate-200 bg-white px-4 py-3 text-sm"
			>
				<option value="">Cámara predeterminada</option>

				{#each cameras as camera}
				<option value={camera.deviceId}>
					{camera.label || 'Dispositivo de video'}
				</option>
				{/each}
			</select>

			<p class="mt-2 text-xs text-slate-500">
				Los dispositivos HDMI compatibles aparecerán como cámaras.
			</p>
			</div>
		{:else}
			<div class="max-w-xl">
			<label
				for="video-file"
				class="mb-2 block text-sm font-medium text-slate-700"
			>
				Archivo de colonoscopia
			</label>

			<input
				id="video-file"
				type="file"
				accept="video/*"
				onchange={handleFileChange}
				disabled={isStreaming || isConnecting}
				class="block w-full rounded-lg border border-slate-200 bg-white p-3 text-sm file:mr-4 file:rounded-md file:border-0 file:bg-blue-600 file:px-3 file:py-2 file:text-white"
			/>

			{#if selectedFile}
				<p class="mt-2 text-sm text-slate-500">
				Seleccionado: {selectedFile.name}
				</p>
			{/if}
			</div>
		{/if}

		<div class="mt-6 flex flex-wrap items-center gap-3">
			<button
			onclick={startSession}
			disabled={isConnecting || isStreaming || (sourceType === 'file' && !selectedFile)}
			class="rounded-lg bg-blue-600 px-6 py-3 text-sm font-semibold text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
			>
			{isConnecting ? 'Conectando...' : 'Iniciar detección'}
			</button>

			<button
			onclick={stopSession}
			disabled={!isStreaming}
			class="rounded-lg border border-red-200 bg-red-50 px-6 py-3 text-sm font-semibold text-red-700 hover:bg-red-100 disabled:cursor-not-allowed disabled:opacity-50"
			>
			Detener sesión
			</button>

			<span class="text-sm text-slate-500">
			{status}
			</span>
		</div>

		{#if errorMessage}
			<p class="mt-4 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
			{errorMessage}
			</p>
		{/if}
		</section>

		<section class="grid gap-6 lg:grid-cols-2">
		<div class="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
			<div class="flex items-center justify-between border-b border-slate-200 px-5 py-4">
			<h2 class="font-semibold">Video original</h2>
			<span class="text-xs text-slate-500">Entrada</span>
			</div>

			<div class="relative aspect-video bg-black">
			<video
				bind:this={localVideo}
				autoplay
				muted
				playsinline
				class="h-full w-full object-contain"
			></video>

			{#if !isStreaming}
				<div class="absolute inset-0 flex items-center justify-center bg-slate-950/70 text-sm text-slate-200">
				Sin fuente de video activa
				</div>
			{/if}
			</div>
		</div>

		<div class="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
			<div class="flex items-center justify-between border-b border-slate-200 px-5 py-4">
			<h2 class="font-semibold">Video procesado por IA</h2>
			<span class="text-xs text-slate-500">YOLO26s + ConvNeXt-Tiny</span>
			</div>

			<div class="relative aspect-video bg-black">
			<video
				bind:this={remoteVideo}
				autoplay
				muted
				playsinline
				class="h-full w-full object-contain"
			></video>

			{#if !isConnected}
				<div class="absolute inset-0 flex items-center justify-center bg-slate-950/70 text-sm text-slate-200">
				Esperando transmisión procesada
				</div>
			{/if}
			</div>
		</div>
		</section>

		<section class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
		<div class="rounded-xl border border-slate-200 bg-white shadow-sm p-5">
			<p class="text-sm text-slate-500">Conexión WebRTC</p>
			<p class="mt-2 text-xl font-semibold">
			{isConnected ? 'Conectada' : 'Desconectada'}
			</p>
		</div>

		<div class="rounded-xl border border-slate-200 bg-white shadow-sm p-5">
			<p class="text-sm text-slate-500">Estado ICE</p>
			<p class="mt-2 text-xl font-semibold">{iceState}</p>
		</div>

		<div class="rounded-xl border border-slate-200 bg-white shadow-sm p-5">
			<p class="text-sm text-slate-500">Resolución de entrada</p>
			<p class="mt-2 text-xl font-semibold">{inputResolution}</p>
		</div>

		<div class="rounded-xl border border-slate-200 bg-white shadow-sm p-5">
			<p class="text-sm text-slate-500">Tiempo de sesión</p>
			<p class="mt-2 text-xl font-semibold">
			{formatDuration(elapsedSeconds)}
			</p>
		</div>
		</section>

		<p class="text-center text-xs text-slate-500">
		Prototipo experimental de investigación.
		Las predicciones no constituyen un diagnóstico médico.
		</p>
	</main>
	</div>

	<!-- Elementos auxiliares para archivos de video. -->
	<video
	bind:this={fileVideo}
	muted
	playsinline
	preload="auto"
	aria-hidden="true"
	class="pointer-events-none fixed left-0 top-0 h-px w-px opacity-0"
	></video>

	<canvas
	bind:this={captureCanvas}
	class="hidden"
	></canvas>