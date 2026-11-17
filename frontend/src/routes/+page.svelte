<script lang="ts">
	import { resolve } from '$app/paths';
	import { useSessions } from '$lib/sessions/context.svelte';
	import { statusLabel } from '$lib/sessions/model';
	const sessions = useSessions();
</script>

<svelte:head><title>Inicio · Polyp</title></svelte:head>
<div class="page-heading">
	<h1>Inicio</h1>
	<span class="prototype-label">Prototipo experimental</span>
</div>
<div class="home-content">
	<section class="panel home-intro" aria-labelledby="welcome-title">
		<p class="eyebrow">Asistencia en colonoscopia</p>
		<h2 id="welcome-title">Prepara la fuente. Revisa la asistencia visual.</h2>
		<p>Explora la visualización de video endoscópico y sus anotaciones en una sesión de prueba.</p>
		<p class="muted">
			Apoyo experimental a la visualización. No reemplaza el criterio clínico ni ofrece un
			diagnóstico autónomo.
		</p>
		<div class="actions">
			<a class="button primary" href={resolve('/sessions/new')}>Nueva sesión</a><a
				class="text-link"
				href={resolve('/sessions')}>Ver sesiones</a
			>
		</div>
	</section>
	<div class="entry-grid">
		<section class="panel entry-card">
			<span class="eyebrow">01 · Preparación</span>
			<h2>Preparar asistencia</h2>
			<p class="muted">
				Conecta una cámara o elige un video autorizado y comprueba la vista previa antes de iniciar.
			</p>
			<a class="text-link" href={resolve('/sessions/new')}>Preparar fuente →</a>
		</section>
		<section class="panel entry-card">
			<span class="eyebrow">02 · Orientación</span>
			<h2>Guía rápida</h2>
			<p class="muted">
				Conoce los pasos, los estados de conexión y qué hacer si la asistencia se interrumpe.
			</p>
			<a class="text-link" href={resolve('/help')}>Consultar ayuda →</a>
		</section>
		<section class="panel entry-card">
			<span class="eyebrow">03 · Comodidad</span>
			<h2>Configuración visual</h2>
			<p class="muted">
				Ajusta tema, contraste, tamaño de texto, movimiento y paleta para esta pantalla.
			</p>
			<a class="text-link" href={resolve('/settings')}>Personalizar interfaz →</a>
		</section>
	</div>
	{#if sessions.records.length}
		<section class="panel" aria-labelledby="recent-sessions">
			<h2 id="recent-sessions">Sesiones recientes</h2>
			<p class="hint">Disponibles en esta pestaña hasta recargar la página.</p>
			<ul class="recent-sessions">
				{#each sessions.records.slice(0, 3) as session (session.id)}<li>
						<div>
							<a class="text-link" href={resolve('/sessions/[id]', { id: session.id })}
								>Sesión {session.id.slice(0, 8)}</a
							>
							<p class="hint">
								{new Date(session.createdAt).toLocaleString('es-PE')} · {session.sourceType ===
								'camera'
									? 'Capturadora'
									: 'Video'}
							</p>
						</div>
						<span class="badge">{statusLabel(session.status)}</span>
					</li>{/each}
			</ul>
			<a class="text-link" href={resolve('/sessions')}>Ver todas las sesiones</a>
		</section>
	{/if}
</div>
