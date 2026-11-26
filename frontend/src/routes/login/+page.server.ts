import { fail, redirect } from '@sveltejs/kit';
import { cookieName, destination, issueSession, revokeSession } from '$lib/server/demo';
import type { Actions } from './$types';
export const actions: Actions = { default: async ({request, cookies, url}) => {
	const data = await request.formData();
	if (data.get('email') !== 'demo@endosight.example' || data.get('password') !== 'EndoSight-Demo-2026!') return fail(400,{invalid:true});
	revokeSession(cookies.get(cookieName));
	cookies.set(cookieName,issueSession(),{path:'/',httpOnly:true,sameSite:'lax',secure:url.protocol==='https:',maxAge:28800});
	redirect(303,destination(url.searchParams.get('next'),url.origin));
}};
