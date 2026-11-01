export type SessionStatus = 'prepared' | 'active' | 'finished';
export type Session = {
	id: string;
	sourceType: 'camera' | 'file';
	status: SessionStatus;
	createdAt: string;
	startedAt: string | null;
	finishedAt: string | null;
};
export function startRecord(record: Session, now: string): Session {
	if (record.status === 'finished') throw new Error('La sesión ya finalizó.');
	return { ...record, status: 'active', startedAt: record.startedAt ?? now };
}
export function finishRecord(record: Session, now: string): Session {
	if (record.status === 'finished') return record;
	return { ...record, status: 'finished', finishedAt: now };
}
export function durationSeconds(record: Session, now = Date.now()): number {
	if (!record.startedAt) return 0;
	return Math.max(
		0,
		Math.floor(
			((record.finishedAt ? Date.parse(record.finishedAt) : now) - Date.parse(record.startedAt)) /
				1000
		)
	);
}
export function formatDuration(seconds: number): string {
	return `${String(Math.floor(seconds / 60)).padStart(2, '0')}:${String(seconds % 60).padStart(2, '0')}`;
}
export function statusLabel(status: SessionStatus): string {
	return { prepared: 'Preparada', active: 'Iniciada', finished: 'Finalizada' }[status];
}

export function nowIso(): string {
	return new Date().toISOString();
}
