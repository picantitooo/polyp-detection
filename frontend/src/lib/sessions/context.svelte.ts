import { getContext, setContext } from 'svelte';
import { browser } from '$app/environment';
import { createClientId } from '$lib/utils/client-id';
import { createSession, finishSession, startSession } from '$lib/application/sessions/session-use-cases';
import type { Session } from '$lib/domain/sessions/session';
import { createLocalStorageSessionRepository } from '$lib/infrastructure/sessions/local-storage-session-repository';

const key = Symbol('sessions');

function nowIso(): string {
	return new Date().toISOString();
}

export function createSessionContext() {
	const repository = browser ? createLocalStorageSessionRepository(window.localStorage) : null;
	let records = $state<Session[]>(repository?.load() ?? []);
	function save(nextRecords: Session[]) {
		records = nextRecords;
		repository?.save(records);
	}
	const store = {
		get records() {
			return records;
		},
		find(id: string) {
			return records.find((record) => record.id === id);
		},
		create(sourceType: Session['sourceType']) {
			const record = createSession({ id: createClientId(), sourceType, now: nowIso() });
			save([record, ...records]);
			return record;
		},
		start(id: string) {
			save(startSession(records, id, nowIso()));
		},
		finish(id: string) {
			save(finishSession(records, id, nowIso()));
		}
	};
	setContext(key, store);
	return store;
}
export function useSessions() {
	return getContext<ReturnType<typeof createSessionContext>>(key);
}
