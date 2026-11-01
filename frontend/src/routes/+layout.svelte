<script lang="ts">
	import { resolve } from '$app/paths';
	import './layout.css';
	import favicon from '$lib/assets/favicon.svg';
	import { page } from '$app/state';
	import { afterNavigate } from '$app/navigation';
	import { createSessionContext } from '$lib/sessions/context.svelte';
	import ProcedureWorkspace from '$lib/components/ProcedureWorkspace.svelte';
	let { children } = $props();
	createSessionContext();
	let navigationOpen = $state(false);
	afterNavigate(() => {
		document.getElementById('main')?.scrollTo({ top: 0 });
		navigationOpen = false;
	});
	const links = [
		{ href: '/', label: 'Inicio', pending: false },
		{ href: '/sessions', label: 'Sesiones', pending: false },
		{ href: '/findings', label: 'Hallazgos', pending: true },
		{ href: '/evidence', label: 'Evidencia', pending: true },
		{ href: '/reports', label: 'Informes', pending: true },
		{ href: '/models', label: 'Modelos', pending: true }
	] as const;
	let preparing = $derived(page.url.pathname === '/sessions/new');
	let live = $derived(/^\/sessions\/[^/]+\/live\/?$/.test(page.url.pathname));
</script>

<svelte:head
	><link rel="icon" href={favicon} /><meta
		name="description"
		content="Asistencia endoscópica para investigación."
	/></svelte:head
>
<a href="#main" class="skip-link">Saltar al contenido</a>
<div class="application" class:procedure-mode={live} class:has-workspace={preparing || live}>
	<aside class="sidebar" class:nav-open={navigationOpen} aria-label="Barra lateral">
		<div class="brand-row">
			<a href={resolve('/')} class="brand">Polyp<span>Endoscopia</span></a><button
				class="nav-toggle"
				aria-expanded={navigationOpen}
				aria-controls="app-navigation"
				onclick={() => (navigationOpen = !navigationOpen)}>Menú</button
			>
		</div>
		<div id="app-navigation" class="navigation-content">
			<nav aria-label="Principal">
				{#each links as link (link.href)}<a
						href={resolve(link.href)}
						class:planned={link.pending}
						class:current={link.href === '/'
							? page.url.pathname === '/'
							: page.url.pathname.startsWith(link.href)}
						aria-current={(
							link.href === '/'
								? page.url.pathname === '/'
								: page.url.pathname.startsWith(link.href)
						)
							? 'page'
							: undefined}
						aria-label={link.pending ? `${link.label} (pendiente)` : link.label}>{link.label}</a
					>{/each}
			</nav>
			<div class="sidebar-bottom">
				<nav aria-label="Aplicación">
					<a
						href={resolve('/settings')}
						class:current={page.url.pathname === '/settings'}
						aria-current={page.url.pathname === '/settings' ? 'page' : undefined}>Configuración</a
					><a
						href={resolve('/help')}
						class:current={page.url.pathname === '/help'}
						aria-current={page.url.pathname === '/help' ? 'page' : undefined}>Ayuda</a
					>
				</nav>
				<span class="sidebar-foot">Versión Beta</span>
			</div>
		</div>
	</aside>
	<div class="application-body">
		<main id="main" class="main-content" class:workspace-main={preparing || live}>
			{#if preparing || live}<ProcedureWorkspace
					{preparing}
					sessionId={page.params.id ?? ''}
				/>{:else}{@render children()}{/if}
		</main>
	</div>
</div>
