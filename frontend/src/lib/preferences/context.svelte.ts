import { getContext, onMount, setContext } from 'svelte';

export const defaults = {
	theme: 'light',
	contrast: 'normal',
	textSize: 'normal',
	reducedMotion: false,
	readingFont: false,
	readingSpacing: false,
	highlightLinks: false,
	defaultVideo: 'annotated',
	showProcessingStatus: true,
	palette: 'standard'
} as const;
export type Preferences = {
	theme: 'system' | 'light' | 'dark';
	contrast: 'normal' | 'high';
	textSize: 'normal' | 'large' | 'extra-large';
	reducedMotion: boolean;
	readingFont: boolean;
	readingSpacing: boolean;
	highlightLinks: boolean;
	defaultVideo: 'annotated' | 'original';
	showProcessingStatus: boolean;
	palette: 'standard' | 'red-green' | 'tritanopia';
};
const key = Symbol('display-preferences');
const storageKey = 'polyp.display-preferences.v1';

function parse(value: unknown): Preferences {
	const result: Preferences = { ...defaults };
	if (!value || typeof value !== 'object') return result;
	const saved = value as Record<string, unknown>;
	if (['system', 'light', 'dark'].includes(String(saved.theme)))
		result.theme = saved.theme as Preferences['theme'];
	if (saved.contrast === 'high') result.contrast = 'high';
	if (saved.textSize === 'large' || saved.textSize === 'extra-large')
		result.textSize = saved.textSize;
	if (typeof saved.reducedMotion === 'boolean') result.reducedMotion = saved.reducedMotion;
	for (const option of ['readingFont', 'readingSpacing', 'highlightLinks'] as const)
		result[option] = saved[option] === true;
	if (saved.defaultVideo === 'original') result.defaultVideo = 'original';
	if (typeof saved.showProcessingStatus === 'boolean') result.showProcessingStatus = saved.showProcessingStatus;
	if (saved.palette === 'red-green' || saved.palette === 'tritanopia')
		result.palette = saved.palette;
	return result;
}

export function createPreferences() {
	let value = $state<Preferences>({ ...defaults });
	let storageAvailable = $state(true);
	let ready = $state(false);
	let systemTheme: MediaQueryList;
	function apply() {
		const root = document.documentElement;
		root.dataset.theme = value.theme;
		root.dataset.colorScheme =
			value.theme === 'system' ? (systemTheme.matches ? 'dark' : 'light') : value.theme;
		root.dataset.contrast = value.contrast;
		root.dataset.textSize = value.textSize;
		root.dataset.reducedMotion = String(value.reducedMotion);
		root.dataset.palette = value.palette;
		root.dataset.readingFont = String(value.readingFont);
		root.dataset.readingSpacing = String(value.readingSpacing);
		root.dataset.highlightLinks = String(value.highlightLinks);
	}
	onMount(() => {
		systemTheme = window.matchMedia('(prefers-color-scheme: dark)');
		try {
			value = parse(JSON.parse(localStorage.getItem(storageKey) ?? 'null'));
		} catch {
			storageAvailable = false;
		}
		apply();
		ready = true;
		systemTheme.addEventListener('change', apply);
		return () => systemTheme.removeEventListener('change', apply);
	});
	function save(next: Preferences) {
		value = next;
		apply();
		try {
			localStorage.setItem(storageKey, JSON.stringify(value));
			storageAvailable = true;
		} catch {
			storageAvailable = false;
		}
	}
	const store = {
		get value() {
			return value;
		},
		get ready() {
			return ready;
		},
		get storageAvailable() {
			return storageAvailable;
		},
		update<K extends keyof Preferences>(name: K, setting: Preferences[K]) {
			save({ ...value, [name]: setting });
		},
		reset() {
			save({ ...defaults });
		}
	};
	setContext(key, store);
	return store;
}
export function usePreferences() {
	return getContext<ReturnType<typeof createPreferences>>(key);
}
