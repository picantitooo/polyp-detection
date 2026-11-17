<script lang="ts">
	import { usePreferences, type Preferences } from '$lib/preferences/context.svelte';
	const preferences = usePreferences();
	let message = $state('');
</script>

<div class="page-heading">
	<div>
		<h1>Configuración</h1>
		<p class="muted">Visualización y accesibilidad para trabajar con comodidad.</p>
	</div>
</div>
<section class="panel preferences-panel" aria-labelledby="display-title">
	<h2 id="display-title">Preferencias de visualización</h2>
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
			? message || 'Guardado local automático. Solo se conservan estas preferencias visuales.'
			: 'El almacenamiento local no está disponible. Las preferencias se aplican durante esta visita.'}
	</p>
</section>
