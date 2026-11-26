import { redirect } from '@sveltejs/kit';
import { cookieName, revokeSession } from '$lib/server/demo';
import type { RequestHandler } from './$types';
export const POST: RequestHandler = ({cookies, url}) => {
	revokeSession(cookies.get(cookieName));
	cookies.delete(cookieName,{path:'/', secure:url.protocol === 'https:', sameSite:'lax', httpOnly:true});
	redirect(303,'/login');
};
