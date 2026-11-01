
<script lang="ts">
  import { onDestroy } from 'svelte';

  const API_URL = 'http://localhost:8000';

  // Referencias a los elementos de video.
  let localVideo: HTMLVideoElement;
  let remoteVideo: HTMLVideoElement;

  // Objetos WebRTC.
  let peerConnection: RTCPeerConnection | null = null;
  let localStream: MediaStream | null = null;

  // Estado reactivo de Svelte 5.
  let status = $state('Desconectado');
  let errorMessage = $state('');
  let isConnecting = $state(false);
  let isConnected = $state(false);
  let isStreaming = $state(false);

  let iceState = $state('new');
  let signalingState = $state('stable');

  /**
   * Espera a que el navegador termine
   * de recopilar candidatos ICE.
   */
  async function waitForIceGathering(
    pc: RTCPeerConnection
  ): Promise<void> {
    if (pc.iceGatheringState === 'complete') {
      return;
    }

    await new Promise<void>((resolve, reject) => {
      const timeout = setTimeout(() => {
        pc.removeEventListener(
          'icegatheringstatechange',
          checkState
        );

        reject(
          new Error('Tiempo de espera ICE agotado')
        );
      }, 10000);

      function checkState() {
        if (pc.iceGatheringState === 'complete') {
          clearTimeout(timeout);

          pc.removeEventListener(
            'icegatheringstatechange',
            checkState
          );

          resolve();
        }
      }

      pc.addEventListener(
        'icegatheringstatechange',
        checkState
      );

      checkState();
    });
  }

  /**
   * Inicia la captura de cámara y
   * establece la conexión WebRTC.
   */
  async function startConnection() {
    if (isConnecting || peerConnection) {
      return;
    }

    isConnecting = true;
    errorMessage = '';
    status = 'Solicitando acceso a cámara...';

    try {
      // 1. Capturar webcam.
      localStream =
        await navigator.mediaDevices.getUserMedia({
          video: {
            width: { ideal: 640 },
            height: { ideal: 480 },
            frameRate: { ideal: 24 }
          },
          audio: false
        });

      localVideo.srcObject = localStream;

      await localVideo.play();

      // 2. Crear conexión WebRTC.
      const pc = new RTCPeerConnection({
        iceServers: []
      });

      peerConnection = pc;
      isStreaming = true;

      // 3. Monitorear estado de conexión.
      pc.onconnectionstatechange = () => {
        console.log(
          '[WebRTC] Connection:',
          pc.connectionState
        );

        // Ignorar eventos de conexiones antiguas.
        if (peerConnection !== pc) {
          return;
        }

        status = `WebRTC: ${pc.connectionState}`;

        isConnected =
          pc.connectionState === 'connected';

        if (pc.connectionState === 'failed') {
          errorMessage =
            'La conexión WebRTC falló.';
        }
      };

      pc.oniceconnectionstatechange = () => {
        console.log(
          '[WebRTC] ICE:',
          pc.iceConnectionState
        );

        if (peerConnection === pc) {
          iceState = pc.iceConnectionState;
        }
      };

      pc.onsignalingstatechange = () => {
        console.log(
          '[WebRTC] Signaling:',
          pc.signalingState
        );

        if (peerConnection === pc) {
          signalingState = pc.signalingState;
        }
      };

      // 4. Recibir video del backend.
      pc.ontrack = (event) => {
        console.log(
          '[WebRTC] Pista recibida:',
          event.track.kind
        );

        if (
          peerConnection !== pc ||
          event.track.kind !== 'video'
        ) {
          return;
        }

        const stream =
          event.streams[0] ??
          new MediaStream([event.track]);

        remoteVideo.srcObject = stream;

        remoteVideo.play().catch((error) => {
          console.error(
            'Error reproduciendo video remoto:',
            error
          );
        });
      };

      // 5. Enviar pistas locales.
      for (const track of localStream.getTracks()) {
        pc.addTrack(track, localStream);
      }

      // 6. Generar oferta SDP.
      status = 'Generando oferta SDP...';

      const offer = await pc.createOffer();

      await pc.setLocalDescription(offer);

      await waitForIceGathering(pc);

      if (!pc.localDescription) {
        throw new Error(
          'No se pudo generar la oferta SDP.'
        );
      }

      // 7. Enviar oferta a FastAPI.
      status = 'Negociando con FastAPI...';

      const response = await fetch(
        `${API_URL}/webrtc/offer`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            sdp: pc.localDescription.sdp,
            type: pc.localDescription.type
          })
        }
      );

      if (!response.ok) {
        const detail = await response.text();

        throw new Error(
          `Error HTTP ${response.status}: ${detail}`
        );
      }

      const answer = await response.json();

      // Si el usuario detuvo la conexión mientras
      // se esperaba la respuesta, no continuar.
      if (peerConnection !== pc) {
        return;
      }

      // 8. Establecer respuesta remota.
      await pc.setRemoteDescription(
        new RTCSessionDescription(answer)
      );

      console.log(
        '[WebRTC] Respuesta SDP establecida'
      );

      if (pc.connectionState !== 'connected') {
        status = `WebRTC: ${pc.connectionState}`;
      }
    } catch (error) {
      console.error('[WebRTC] Error:', error);

      const message =
        error instanceof Error
          ? error.message
          : 'Error desconocido';

      stopConnection();
      errorMessage = message;
    } finally {
      isConnecting = false;
    }
  }

  /**
   * Detiene la transmisión y libera
   * los recursos del navegador.
   */
  function stopConnection() {
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

    isConnected = false;
    isConnecting = false;
    isStreaming = false;

    iceState = 'closed';
    signalingState = 'closed';

    status = 'Desconectado';
  }

  onDestroy(() => {
    stopConnection();
  });
</script>

<svelte:head>
  <title>Video procesado por IA | Polyp Detection</title>
</svelte:head>

<main class="mx-auto max-w-6xl p-6">
    <h1 class="mb-2 text-3xl font-bold">
    Detección de pólipos en tiempo real
    </h1>

    <p class="mb-6 text-gray-500">
    Transmisión WebRTC con inferencia ONNX mediante
    YOLO26s y ConvNeXt-Tiny.
    </p>

  <div class="mb-6 flex flex-wrap items-center gap-4">
    <button
      onclick={startConnection}
      disabled={isConnecting || isStreaming}
      class="rounded-lg bg-blue-600 px-5 py-3 font-medium text-white disabled:opacity-50"
    >
      {isConnecting
        ? 'Conectando...'
        : 'Iniciar transmisión'}
    </button>

    <button
      onclick={stopConnection}
      disabled={!isStreaming}
      class="rounded-lg bg-red-600 px-5 py-3 font-medium text-white disabled:opacity-50"
    >
      Detener
    </button>

    <span class="text-sm font-medium">
      Estado: {status}
    </span>
  </div>

  {#if errorMessage}
    <div
      class="mb-5 rounded-lg bg-red-100 p-4 text-red-700"
    >
      {errorMessage}
    </div>
  {/if}

  <div class="grid gap-6 md:grid-cols-2">
    <section class="overflow-hidden rounded-xl border">
      <h2 class="p-4 text-lg font-semibold">
        Video local
      </h2>

      <video
        bind:this={localVideo}
        autoplay
        muted
        playsinline
        class="aspect-video w-full bg-black object-contain"
      ></video>
    </section>

    <section class="overflow-hidden rounded-xl border">
      <h2 class="p-4 text-lg font-semibold">
        Video recibido desde FastAPI
      </h2>

      <video
        bind:this={remoteVideo}
        autoplay
        muted
        playsinline
        class="aspect-video w-full bg-black object-contain"
      ></video>
    </section>
  </div>

  <div class="mt-6 rounded-lg border p-4">
    <h3 class="mb-3 font-semibold">
      Diagnóstico WebRTC
    </h3>

    <div class="grid gap-3 text-sm sm:grid-cols-2">
      <div>
        <span class="text-gray-500">
          Conexión establecida:
        </span>

        <span
          class:font-semibold={isConnected}
          class:text-green-600={isConnected}
        >
          {isConnected ? 'Sí' : 'No'}
        </span>
      </div>

      <div>
        <span class="text-gray-500">
          Estado ICE:
        </span>
        {iceState}
      </div>

      <div>
        <span class="text-gray-500">
          Señalización:
        </span>
        {signalingState}
      </div>

      <div>
        <span class="text-gray-500">
          Cámara activa:
        </span>
        {isStreaming ? 'Sí' : 'No'}
      </div>
    </div>
  </div>
</main>
