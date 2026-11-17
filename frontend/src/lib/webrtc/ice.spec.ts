import { afterEach, describe, expect, it, vi } from 'vitest';
import { fetchIceServers, parseIceServers, turnConnectivityError } from './ice';

afterEach(() => vi.unstubAllGlobals());
describe('ICE configuration', () => {
	it('supports local mode and ephemeral TURN', () => {
		expect(parseIceServers({ iceServers: [] })).toEqual([]);
		expect(
			parseIceServers({
				iceServers: [
					{ urls: 'turn:example.test:3478', username: '123:abc', credential: 'temporary' }
				]
			})
		).toEqual([{ urls: ['turn:example.test:3478'], username: '123:abc', credential: 'temporary' }]);
	});
	it.each([
		null,
		{},
		{ iceServers: null },
		{ iceServers: [{}] },
		{ iceServers: [{ urls: [] }] },
		{ iceServers: [{ urls: 'https://example.test' }] },
		{ iceServers: [{ urls: 'turn:example.test' }] },
		{ iceServers: [{ urls: 'turn:user:secret@example.test', username: 'u', credential: 's' }] }
	])('rejects invalid configuration %#', (value) => {
		expect(() => parseIceServers(value)).toThrow();
	});
	it('fetches configuration from the compiled API URL without caching', async () => {
		const fetcher = vi.fn().mockResolvedValue({ ok: true, json: async () => ({ iceServers: [] }) });
		vi.stubGlobal('fetch', fetcher);
		expect(await fetchIceServers('http://proxy.example.test/api')).toEqual([]);
		expect(fetcher).toHaveBeenCalledWith('http://proxy.example.test/api/webrtc/ice-servers', {
			cache: 'no-store',
			signal: undefined
		});
	});
	it.each(['network', 'http', 'json', 'shape'])(
		'provides a safe message for %s failures',
		async (failure) => {
			vi.stubGlobal(
				'fetch',
				vi.fn(async () => {
					if (failure === 'network') throw new Error('sensitive');
					return {
						ok: failure !== 'http',
						json: async () => {
							if (failure === 'json') throw new Error('sensitive');
							return { sensitive: 'sensitive' };
						}
					};
				})
			);
			await expect(fetchIceServers('/api')).rejects.toThrow(
				'No se pudo obtener la configuración ICE'
			);
			expect(turnConnectivityError).not.toContain('sensitive');
		}
	);
});
