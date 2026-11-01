import { getContext, setContext } from 'svelte';
import { startRecord, finishRecord, nowIso, type Session } from './model';
const key = Symbol('sessions');
export function createSessionContext() {
	let records = $state<Session[]>([]);
	const store = {
		get records() {
			return records;
		},
		find(id: string) {
			return records.find((record) => record.id === id);
		},
		create(sourceType: Session['sourceType']) {
			const record: Session = {
				id: crypto.randomUUID(),
				sourceType,
				status: 'prepared',
				createdAt: nowIso(),
				startedAt: null,
				finishedAt: null
			};
			records = [record, ...records];
			return record;
		},
		start(id: string) {
			records = records.map((record) =>
				record.id === id ? startRecord(record, nowIso()) : record
			);
		},
		finish(id: string) {
			records = records.map((record) =>
				record.id === id ? finishRecord(record, nowIso()) : record
			);
		}
	};
	setContext(key, store);
	return store;
}
export function useSessions() {
	return getContext<ReturnType<typeof createSessionContext>>(key);
}
