import { finishRecord, startRecord, type Session } from '$lib/domain/sessions/session';

export function createSession(input: {
	id: string;
	sourceType: Session['sourceType'];
	now: string;
}): Session {
	return {
		id: input.id,
		sourceType: input.sourceType,
		status: 'prepared',
		createdAt: input.now,
		startedAt: null,
		finishedAt: null
	};
}

export function startSession(records: Session[], id: string, now: string): Session[] {
	return records.map((record) => (record.id === id ? startRecord(record, now) : record));
}

export function finishSession(records: Session[], id: string, now: string): Session[] {
	return records.map((record) => (record.id === id ? finishRecord(record, now) : record));
}
