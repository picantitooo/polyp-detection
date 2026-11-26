import { error, redirect, type Handle } from '@sveltejs/kit';
import { cookieName, demoEnabled, validSession } from '$lib/server/demo';
export const handle: Handle = async ({event, resolve}) => {
	const enabled = demoEnabled(event.url);
	if (!enabled && (event.url.hostname === 'demo.localhost' || ['/login','/logout'].includes(event.url.pathname))) error(404);
	if (enabled && event.route.id !== '/login' && !validSession(event.cookies.get(cookieName))) {
		redirect(303, '/login?next=' + encodeURIComponent(event.url.pathname + event.url.search));
	}
	const response = await resolve(event);
	if (enabled) response.headers.set('cache-control','private, no-store');
	return response;
};
