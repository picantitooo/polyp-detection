import type { SessionReport } from '$lib/application/sessions/session-report';

export type Detection = {
	capturedAt: string;
	videoSeconds: number | null;
	label: string;
	confidence: number;
	detectionConfidence: number;
	jpeg: string;
};

export type Evidence = Detection & { id: string; sessionId: string };
export type Finding = {
	id: string;
	sessionId: string;
	evidenceIds: string[];
	decision: 'Revisado' | 'Descartado' | 'No concluyente';
	note: string;
};

export function parseDetection(message: unknown): Detection | null {
	if (typeof message !== 'string' || message.length > 65536) return null;
	try {
		const data = JSON.parse(message);
		if (!data || typeof data.label !== 'string' || data.label.length > 40 ||
			typeof data.capturedAt !== 'string' || !Number.isFinite(Date.parse(data.capturedAt)) ||
			typeof data.jpeg !== 'string' || !/^[A-Za-z0-9+/]+={0,2}$/.test(data.jpeg) ||
			![data.confidence, data.detectionConfidence].every((value) =>
				typeof value === 'number' && value >= 0 && value <= 1) ||
			(data.videoSeconds !== null && !Number.isFinite(data.videoSeconds))) return null;
		return data as Detection;
	} catch {
		return null;
	}
}

function openDatabase(): Promise<IDBDatabase> {
	return new Promise((resolve, reject) => {
		const request = indexedDB.open('endosight-session-evidence', 2);
		request.onupgradeneeded = (event) => {
			if (event.oldVersion < 1) {
				request.result.createObjectStore('evidence', { keyPath: 'id' });
				request.result.createObjectStore('findings', { keyPath: 'id' });
			}
			if (event.oldVersion < 2) {
				const reports = request.result.createObjectStore('reports', { keyPath: 'id' });
				reports.createIndex('session', 'session.id', { unique: true });
			}
		};
		request.onsuccess = () => resolve(request.result);
		request.onerror = () => reject(request.error);
		request.onblocked = () => reject(new Error('Cierra otras pestañas de EndoSight para actualizar el almacenamiento.'));
	});
}

async function access<T>(
	store: 'evidence' | 'findings' | 'reports',
	mode: IDBTransactionMode,
	run: (table: IDBObjectStore) => IDBRequest<T>
): Promise<T> {
	const database = await openDatabase();
	try {
		return await new Promise((resolve, reject) => {
			const transaction = database.transaction(store, mode);
			const request = run(transaction.objectStore(store));
			transaction.oncomplete = () => resolve(request.result);
			transaction.onabort = () => reject(transaction.error ?? request.error);
		});
	} finally {
		database.close();
	}
}

export const saveEvidence = (item: Evidence) => access('evidence', 'readwrite', (table) => table.add(item));
export const saveFinding = (item: Finding) => access('findings', 'readwrite', (table) => table.add(item));
export const listEvidence = (): Promise<Evidence[]> => access('evidence', 'readonly', (table) => table.getAll());
export const listFindings = (): Promise<Finding[]> => access('findings', 'readonly', (table) => table.getAll());
export const listReports = (): Promise<SessionReport[]> => access('reports', 'readonly', (table) => table.getAll());
export const addReport = (report: SessionReport) => access('reports', 'readwrite', (table) => table.add(report));
export const saveReport = (report: SessionReport) => access('reports', 'readwrite', (table) => table.put(report));
export const evidenceImage = (item: Evidence) => `data:image/jpeg;base64,${item.jpeg}`;
