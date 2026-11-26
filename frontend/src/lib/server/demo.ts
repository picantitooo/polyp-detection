import { dev } from '$app/environment';
import { env } from '$env/dynamic/private';
import { randomUUID } from 'node:crypto';

export const cookieName = 'endosight_demo';
const lifetime = 8 * 60 * 60;
const sessions = new Map<string, number>();
export const demoEnabled = (url: URL) =>
	dev && env.ENDOSIGHT_DEMO !== 'false' && ['127.0.0.1', 'localhost', 'demo.localhost', '[::1]'].includes(url.hostname);

export function issueSession() {
	for (const [id, until] of sessions) if (until <= Date.now()) sessions.delete(id);
	const id = randomUUID();
	sessions.set(id, Date.now() + lifetime * 1000);
	return id;
}
export const validSession = (id = '') => (sessions.get(id) ?? 0) > Date.now();
export const revokeSession = (id = '') => sessions.delete(id);
export function destination(value: string | null, origin: string) {
	if (!value?.startsWith('/') || /[\\\s]/.test(value)) return '/';
	const target = new URL(value, origin);
	return target.origin === origin && !target.pathname.startsWith('//') && !['/login','/logout'].includes(target.pathname)
		? target.pathname + target.search : '/';
}

