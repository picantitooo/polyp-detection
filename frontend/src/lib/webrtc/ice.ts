export const turnConnectivityError =
	'No se pudo contactar un servidor ICE/TURN. Comprueba tu red y los puertos TURN; puedes reintentar.';

export function parseIceServers(value: unknown): RTCIceServer[] {
	if (
		!value ||
		typeof value !== 'object' ||
		!('iceServers' in value) ||
		!Array.isArray(value.iceServers)
	) {
		throw new Error('Configuración ICE inválida. Comprueba la API e intenta de nuevo.');
	}
	return value.iceServers.map((server: unknown) => {
		if (!server || typeof server !== 'object' || !('urls' in server)) {
			throw new Error('Configuración ICE inválida.');
		}
		const urls = typeof server.urls === 'string' ? [server.urls] : server.urls;
		if (
			!Array.isArray(urls) ||
			!urls.length ||
			!urls.every(
				(url: unknown) => typeof url === 'string' && /^(turn|turns|stun|stuns):[^\s@]+$/.test(url)
			)
		) {
			throw new Error('Configuración ICE inválida.');
		}
		const usesTurn = urls.some((url: string) => /^turns?:/.test(url));
		if (
			usesTurn &&
			(!('username' in server) ||
				typeof server.username !== 'string' ||
				!server.username ||
				!('credential' in server) ||
				typeof server.credential !== 'string' ||
				!server.credential)
		) {
			throw new Error('Configuración TURN incompleta.');
		}
		return {
			urls: [...urls],
			...(usesTurn
				? {
						username: (server as RTCIceServer).username,
						credential: (server as RTCIceServer).credential
					}
				: {})
		};
	});
}

export async function fetchIceServers(
	apiUrl: string,
	signal?: AbortSignal
): Promise<RTCIceServer[]> {
	try {
		const response = await fetch(`${apiUrl}/webrtc/ice-servers`, { signal, cache: 'no-store' });
		if (!response.ok) throw new Error('ICE request failed');
		return parseIceServers(await response.json());
	} catch {
		// Never propagate server bodies, URLs with userinfo or credentials to UI/logs.
		throw new Error(
			'No se pudo obtener la configuración ICE. Comprueba la API y tu conexión; intenta de nuevo.'
		);
	}
}
