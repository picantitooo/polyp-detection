import { describe, expect, it } from 'vitest';
import { createLocalStorageSessionRepository } from './local-storage-session-repository';

function createMemoryStorage(): Storage {
	const entries = new Map<string, string>();
	return {
		get length() {
			return entries.size;
		},
		clear: () => entries.clear(),
		getItem: (key) => entries.get(key) ?? null,
		key: (index) => [...entries.keys()][index] ?? null,
		removeItem: (key) => entries.delete(key),
		setItem: (key, value) => entries.set(key, value)
	};
}

describe('local storage session repository', () => {
	it('restores only valid session records', () => {
		const storage = createMemoryStorage();
		storage.setItem(
			'polyp.sessions.v1',
			JSON.stringify([
				{
					id: 'valid',
					sourceType: 'camera',
					status: 'prepared',
					createdAt: '2026-11-16T10:00:00.000Z',
					startedAt: null,
					finishedAt: null
				},
				{ invalid: true }
			])
		);

		expect(createLocalStorageSessionRepository(storage).load()).toHaveLength(1);
	});
});
