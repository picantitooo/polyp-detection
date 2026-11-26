import { demoEnabled } from '$lib/server/demo';
import type { LayoutServerLoad } from './$types';
export const load: LayoutServerLoad = ({url}) => ({ demo: demoEnabled(url) });
