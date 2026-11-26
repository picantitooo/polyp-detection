<script lang="ts">
	import { usePreferences, type Preferences } from '$lib/preferences/context.svelte';
	import { onMount } from 'svelte';
	let { embedded = false }: { embedded?: boolean } = $props();
	const preferences = usePreferences();
	let message = $state('');
	let canSpeak = $state(false);
	const readingOptions = [
		{ key: 'readingFont', label: 'Tipografía de lectura clara' },
		{ key: 'readingSpacing', label: 'Aumentar el espaciado de lectura' },
		{ key: 'highlightLinks', label: 'Resaltar los enlaces' }
	] as const;
	onMount(() => {
		canSpeak = 'speechSynthesis' in window;
		return () => window.speechSynthesis?.cancel();
	});
	function readSelection() {
		const selection = window.getSelection()?.toString().trim();
		if (!selection) {
			message = 'Selecciona el texto que quieres escuchar.';
			return;
		}
		const speech = new SpeechSynthesisUtterance(selection);
		speech.lang = 'es-PE';
		window.speechSynthesis.cancel();
		window.speechSynthesis.speak(speech);
	}
</script>

{#if embedded}
	<div class="accessibility-options" role="group" aria-label="Ajustes de accesibilidad">
		<button aria-pressed={preferences.value.contrast === 'high'} onclick={() => preferences.update('contrast', preferences.value.contrast === 'high' ? 'normal' : 'high')}><span class="accessibility-icon" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18Zm0 0v18" /></svg></span>Alto contraste</button>
		<button aria-pressed={preferences.value.textSize !== 'normal'} onclick={() => preferences.update('textSize', preferences.value.textSize === 'normal' ? 'large' : 'normal')}><span class="accessibility-icon" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M3 19l6-14 6 14M5 14h8m6-6v8m-4-4h8" /></svg></span>Texto grande</button>
		<button aria-pressed={preferences.value.readingFont} onclick={() => preferences.update('readingFont', !preferences.value.readingFont)}><span class="accessibility-icon" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M4 5h6a2 2 0 0 1 2 2v13a4 4 0 0 0-4-3H4zM20 5h-6a2 2 0 0 0-2 2v13a4 4 0 0 1 4-3h4z" /></svg></span>Lectura clara</button>
		<button aria-pressed={preferences.value.readingSpacing} onclick={() => preferences.update('readingSpacing', !preferences.value.readingSpacing)}><span class="accessibility-icon" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M8 8l-4 4 4 4m8-8 4 4-4 4M4 12h16" /></svg></span>Espaciado de texto</button>
		<button aria-pressed={preferences.value.highlightLinks} onclick={() => preferences.update('highlightLinks', !preferences.value.highlightLinks)}><span class="accessibility-icon" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M10 8H7a4 4 0 0 0 0 8h3m4-8h3a4 4 0 0 1 0 8h-3m-6-4h8" /></svg></span>Resaltar enlaces</button>
		<button aria-pressed={preferences.value.reducedMotion} onclick={() => preferences.update('reducedMotion', !preferences.value.reducedMotion)}><span class="accessibility-icon" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M9 8v8m6-8v8M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18Z" /></svg></span>Reducir movimiento</button>
	</div>
	<div class="accessibility-footer">
		{#if preferences.value.theme !== 'light'}
			<button onclick={() => preferences.update('theme', 'light')}>Volver al tema claro</button>
		{/if}
		<button class="accessibility-reset" onclick={() => preferences.reset()}>Restablecer ajustes</button>
	</div>
{:else}
<div class="page-heading">
	<div>
		<h1>Accesibilidad</h1>
		<p class="muted">Visualización y accesibilidad para trabajar con comodidad.</p>
	</div>
</div>
<section class="panel preferences-panel" aria-label="Preferencias de visualización y lectura">
	<h2>{embedded ? 'Accesibilidad' : 'Preferencias de visualización'}</h2>
	<p class="muted">
		Se aplican a toda la interfaz y se guardan en este navegador. La paleta cambia los controles,
		sin modificar el video ni sus anotaciones.
	</p>
	<fieldset disabled={!preferences.ready}>
		<legend class="visually-hidden">Personalizar la interfaz</legend>
		<div class="preferences-grid">
			<div class="preference-field">
				<label for="display-theme">Tema</label><select
					id="display-theme"
					value={preferences.value.theme}
					onchange={(e) =>
						preferences.update('theme', e.currentTarget.value as Preferences['theme'])}
					><option value="system">Sistema</option><option value="light">Claro</option><option
						value="dark">Oscuro</option
					></select
				>
				<p class="hint">Sistema sigue la apariencia del dispositivo.</p>
			</div>
			<div class="preference-field">
				<label for="display-contrast">Contraste</label><select
					id="display-contrast"
					value={preferences.value.contrast}
					onchange={(e) =>
						preferences.update('contrast', e.currentTarget.value as Preferences['contrast'])}
					><option value="normal">Normal</option><option value="high">Alto contraste</option
					></select
				>
			</div>
			<div class="preference-field">
				<label for="display-size">Tamaño de texto</label><select
					id="display-size"
					value={preferences.value.textSize}
					onchange={(e) =>
						preferences.update('textSize', e.currentTarget.value as Preferences['textSize'])}
					><option value="normal">Normal</option><option value="large">Grande</option><option
						value="extra-large">Extra grande</option
					></select
				>
			</div>
			<div class="preference-field">
				<label for="display-palette">Paleta de la interfaz</label><select
					id="display-palette"
					value={preferences.value.palette}
					onchange={(e) =>
						preferences.update('palette', e.currentTarget.value as Preferences['palette'])}
					><option value="standard">Estándar</option><option value="red-green"
						>Deuteranopia / protanopia</option
					><option value="tritanopia">Tritanopia</option></select
				>
			</div>
		</div>
		<h3 class="reading-heading">Apoyos de lectura y dislexia</h3>
		{#each readingOptions as option (option.key)}
			<label class="checkbox-label">
				<input type="checkbox" checked={preferences.value[option.key]}
					onchange={(event) => preferences.update(option.key, event.currentTarget.checked)} />
				{option.label}
			</label>
		{/each}
		<label class="checkbox-label" for="display-motion"
			><input
				id="display-motion"
				type="checkbox"
				checked={preferences.value.reducedMotion}
				onchange={(e) => preferences.update('reducedMotion', e.currentTarget.checked)}
			/><span
				>Reducir animaciones<span class="hint"
					>También se respeta la preferencia de movimiento reducido del dispositivo.</span
				></span
			></label
		>
		<div class="actions">
			{#if canSpeak}
				<button onclick={readSelection}>Leer selección en voz alta</button>
				<button onclick={() => window.speechSynthesis.cancel()}>Detener lectura</button>
			{/if}
			<button
				onclick={() => {
					preferences.reset();
					message = 'Preferencias restablecidas.';
				}}>Restablecer preferencias</button
			>
		</div>
	</fieldset>
	<p class="hint" role="status">
		{preferences.storageAvailable
			? message || 'Tus preferencias visuales se guardan automáticamente en este navegador.'
			: 'El almacenamiento local no está disponible. Las preferencias se aplican durante esta visita.'}
	</p>
</section>
{/if}
