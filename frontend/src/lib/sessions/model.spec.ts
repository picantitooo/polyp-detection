import { describe, expect, it } from 'vitest';
import { startRecord, finishRecord, durationSeconds, type Session } from './model';
const base: Session = {
	id: 'test',
	sourceType: 'camera',
	status: 'prepared',
	createdAt: '2026-11-01T10:00:00Z',
	startedAt: null,
	finishedAt: null
};
describe('session lifecycle', () => {
	it('keeps the first start when assistance reconnects', () => {
		const started = startRecord(base, '2026-11-01T10:01:00Z');
		const resumed = startRecord(started, '2026-11-01T10:02:00Z');
		expect(resumed.startedAt).toBe('2026-11-01T10:01:00Z');
		expect(base.status).toBe('prepared');
	});
	it('finishes idempotently and cannot restart a completed session', () => {
		const finished = finishRecord(
			startRecord(base, '2026-11-01T10:01:00Z'),
			'2026-11-01T10:03:00Z'
		);
		expect(finishRecord(finished, '2026-11-01T10:04:00Z')).toEqual(finished);
		expect(() => startRecord(finished, '2026-11-01T10:05:00Z')).toThrow();
		expect(durationSeconds(finished, Date.parse('2026-11-02T00:00:00Z'))).toBe(120);
	});
	it('does not invent inference time for a session that never connected', () => {
		expect(durationSeconds(finishRecord(base, '2026-11-01T10:05:00Z'))).toBe(0);
	});
});
