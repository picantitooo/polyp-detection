import { describe, expect, it } from 'vitest';
import { createSession, finishSession, startSession } from './session-use-cases';

describe('session use cases', () => {
	it('creates, starts and finishes a session without mutating its previous state', () => {
		const created = createSession({
			id: 'session-1',
			sourceType: 'file',
			now: '2026-11-16T10:00:00.000Z'
		});
		const started = startSession([created], created.id, '2026-11-16T10:01:00.000Z');
		const finished = finishSession(started, created.id, '2026-11-16T10:02:00.000Z');

		expect(created.status).toBe('prepared');
		expect(started[0].startedAt).toBe('2026-11-16T10:01:00.000Z');
		expect(finished[0]).toMatchObject({
			status: 'finished',
			finishedAt: '2026-11-16T10:02:00.000Z'
		});
	});
});
