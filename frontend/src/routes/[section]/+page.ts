import { error } from '@sveltejs/kit';
export function load({ params }: { params: { section: string } }) {
	if (!['findings', 'evidence', 'reports', 'models', 'settings', 'help'].includes(params.section))
		error(404, 'Página no encontrada');
	return { section: params.section };
}
