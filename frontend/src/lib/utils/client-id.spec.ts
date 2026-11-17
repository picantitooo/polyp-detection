import { afterEach, describe, expect, it, vi } from 'vitest';
import { createClientId } from './client-id';

const uuidV4 = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;

afterEach(() => {
	vi.unstubAllGlobals();
	vi.restoreAllMocks();
});

describe('createClientId', () => {
	it('uses randomUUID when available and preserves its receiver', () => {
		const id = '12345678-1234-4567-89ab-123456789abc';
		const crypto = {
			randomUUID: vi.fn(function (this: unknown) {
				expect(this).toBe(crypto);
				return id;
			}),
			getRandomValues: vi.fn()
		};
		vi.stubGlobal('crypto', crypto);

		expect(createClientId()).toBe(id);
		expect(crypto.randomUUID).toHaveBeenCalledOnce();
		expect(crypto.getRandomValues).not.toHaveBeenCalled();
	});

	it.each([0x00, 0xff])('uses getRandomValues without randomUUID (bytes %i)', (fill) => {
		const crypto = {
			getRandomValues: vi.fn(function (this: unknown, bytes: Uint8Array) {
				expect(this).toBe(crypto);
				return bytes.fill(fill);
			})
		};
		vi.stubGlobal('crypto', crypto);
		const random = vi.spyOn(Math, 'random');

		const id = createClientId();

		expect(id).toMatch(uuidV4);
		expect(id).toBe(
			fill === 0x00
				? '00000000-0000-4000-8000-000000000000'
				: 'ffffffff-ffff-4fff-bfff-ffffffffffff'
		);
		expect(crypto.getRandomValues).toHaveBeenCalledExactlyOnceWith(expect.any(Uint8Array));
		expect(random).not.toHaveBeenCalled();
	});

	it.each([undefined, {}])('uses the local UI fallback without Web Crypto (%j)', (crypto) => {
		vi.stubGlobal('crypto', crypto);
		const random = vi.spyOn(Math, 'random').mockReturnValue(0.5);

		expect(createClientId()).toMatch(uuidV4);
		expect(random).toHaveBeenCalledTimes(16);
	});
});
