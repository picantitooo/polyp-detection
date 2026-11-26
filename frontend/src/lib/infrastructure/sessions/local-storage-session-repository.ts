import type { SessionRepository } from '$lib/domain/sessions/session-repository';
import type { Session } from '$lib/domain/sessions/session';

const storageKey = 'polyp.sessions.v1';

function isSession(value: unknown): value is Session {
	if (!value || typeof value !== 'object') return false;
	const record = value as Record<string, unknown>;
	return (
		typeof record.id === 'string' &&
		(record.sourceType === 'camera' || record.sourceType === 'file') &&
		(record.status === 'prepared' || record.status === 'active' || record.status === 'finished') &&
		typeof record.createdAt === 'string' &&
		(record.startedAt === null || typeof record.startedAt === 'string') &&
		(record.finishedAt === null || typeof record.finishedAt === 'string')
	);
}

export function createLocalStorageSessionRepository(storage: Storage): SessionRepository {
	return {
		load() {
			try {
				const saved = storage.getItem(storageKey);
				if (!saved) return [];
				const parsed: unknown = JSON.parse(saved);
				return Array.isArray(parsed) ? parsed.filter(isSession) : [];
			} catch {
				return [];
			}
		},
		save(records) {
			try {
				storage.setItem(storageKey, JSON.stringify(records));
			} catch {
				// The interface remains usable when browser storage is disabled or full.
			}
		}
	};
}
