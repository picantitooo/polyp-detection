<script lang="ts">
	import { resolve } from '$app/paths';
	import './layout.css';
	import favicon from '$lib/assets/favicon.svg';
	import { page } from '$app/state';
	import { afterNavigate } from '$app/navigation';
	import { createPreferences } from '$lib/preferences/context.svelte';
	import { createSessionContext } from '$lib/sessions/context.svelte';
	import ProcedureWorkspace from '$lib/components/ProcedureWorkspace.svelte';
	import DisplayPreferences from '$lib/components/DisplayPreferences.svelte';
	let accessibilityDialog = $state<HTMLDialogElement>(null!);
	let { children, data } = $props();
	createSessionContext();
	createPreferences();
	let accountOpen = $state(false);
 let accountButton = $state<HTMLButtonElement>(null!);
 function handleKey(event: KeyboardEvent) {
  if (accountOpen && event.key === 'Escape') {
   accountOpen = false;
   accountButton.focus();
  }
 }
 let navigationOpen = $state(false);
	const icons = {
		'/': 'm3 10 9-7 9 7v10h-6v-6H9v6H3z',
		'/sessions': 'M6 3h12v18H6zM9 8h6m-6 4h6m-6 4h4',
		'/findings': 'M21 21l-5-5M18 11a7 7 0 1 1-14 0 7 7 0 0 1 14 0Z',
		'/evidence': 'M3 5h18v14H3zM3 16l5-5 4 4 3-3 6 6',
		'/reports': 'M6 3h8l4 4v14H6zM14 3v5h4m-9 5h6m-6 4h6'
	};
	afterNavigate(() => {
		document.getElementById('main')?.scrollTo({ top: 0 });
		navigationOpen = false;
	});
	const links = [
		{ href: '/', label: 'Inicio', pending: false },
		{ href: '/sessions', label: 'Sesiones', pending: false },
		{ href: '/findings', label: 'Hallazgos', pending: false },
		{ href: '/evidence', label: 'Evidencia', pending: false },
		{ href: '/reports', label: 'Informes', pending: false }
	] as const;
	let preparing = $derived(page.route.id === '/sessions/new');
	let live = $derived(page.route.id === '/sessions/[id]/live');
</script>

<svelte:window onkeydown={handleKey} onpageshow={(event) => { if (data.demo && event.persisted) location.reload(); }} />
<svelte:head
	><link rel="icon" href={favicon} /><meta
		name="description"
		content="Asistencia endoscópica para investigación."
	/></svelte:head
>
{#if page.route.id === '/login'}{@render children()}{:else}
<a href="#main" class="skip-link">Saltar al contenido</a>
<div
	class="application"
	class:procedure-mode={live}
	class:has-workspace={preparing || live}
>
	<aside class="sidebar" class:nav-open={navigationOpen} aria-label="Barra lateral">
		<div class="brand-row">
			<a href={resolve('/')} class="brand">
				<span class="brand-symbol" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M6 4a2 2 0 1 0-3 2.8v8a3 3 0 0 0 3 3m0-10v6m0-10c4 2 8 2 12 0a2 2 0 1 1 3 2.8v7a4 4 0 0 1-4 4h-2a2 2 0 0 0-2 2V22h-3v-2a5 5 0 0 1 5-5h2a1 1 0 0 0 1-1V8c-4 2-8 2-12 0" /></svg></span>
				<strong>Endo<b class="brand-accent">Sight</b><small>Asistencia endoscópica</small></strong>
			</a>
			<button
				class="nav-toggle"
				aria-expanded={navigationOpen}
				aria-controls="app-navigation"
				onclick={() => (navigationOpen = !navigationOpen)}>Menú</button
			>
		</div>
		<div id="app-navigation" class="navigation-content">
			<span class="nav-label">Navegación</span>
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
						aria-label={link.pending ? `${link.label} (pendiente)` : link.label}>
						<svg viewBox="0 0 24 24" aria-hidden="true"><path d={icons[link.href]} /></svg>
						{link.label}</a
					>{/each}
			</nav>
			<div class="sidebar-bottom">
				<nav aria-label="Aplicación">
					<a
						href={resolve('/settings')}
						class:current={page.url.pathname === '/settings'}
						aria-current={page.url.pathname === '/settings' ? 'page' : undefined}><svg viewBox="0 0 24 24" aria-hidden="true"><path d="m10 3 4 0 1 3 3 1 3 3-2 2v2l2 2-3 3-3-1-1 3h-4l-1-3-3 1-3-3 2-2v-2l-2-2 3-3 3-1z"/><circle cx="12" cy="12" r="3"/></svg>Configuración</a
					><a
						href={resolve('/help')}
						class:current={page.url.pathname === '/help'}
						aria-current={page.url.pathname === '/help' ? 'page' : undefined}><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M9 9a3 3 0 1 1 4 3c-1 .5-1 1-1 2m0 3h.01"/></svg>Ayuda</a
					>
				</nav>
				<span class="sidebar-foot">Versión de investigación</span>
			</div>
		</div>
	</aside>
	<div class="application-body">
		{#if !live}<header class="app-header">
			<span>Panel de colonoscopia</span>
			<div class="header-tools">
			<button class="accessibility-trigger" aria-haspopup="dialog" onclick={() => accessibilityDialog.showModal()}>
				<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="4" r="1.5" /><path d="M4 8l8 2 8-2M12 10v5m0 0-4 6m4-6 4 6" /></svg>
				Accesibilidad
			</button>
			{#if data.demo}<div class="account">
 <button class="account-trigger" bind:this={accountButton} aria-expanded={accountOpen} aria-label="Cuenta de Médico · Endoscopia" onclick={() => accountOpen = !accountOpen}><span class="avatar" aria-hidden="true">M</span><span class="account-label"><strong>Médico</strong><small>Endoscopia</small></span><svg viewBox="0 0 24 24" aria-hidden="true"><path d="m6 9 6 6 6-6"/></svg></button>
 {#if accountOpen}<div class="account-popup"><small>Cuenta demo</small><form method="POST" action="/logout"><button><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M10 4H4v16h6m5-12 4 4-4 4m-7-4h11"/></svg>Cerrar sesión</button></form></div>{/if}</div>{:else}<div class="header-profile"><span aria-hidden="true">M</span><div><strong>Médico</strong><small>Endoscopia</small></div></div>{/if}
			</div>
		</header>{/if}
		<main id="main" class="main-content" class:workspace-main={preparing || live}>
			{#if preparing || live}<ProcedureWorkspace
					{preparing}
					sessionId={page.params.id ?? ''}
				/>{:else}{@render children()}{/if}
		</main>
	</div>
</div>
<dialog class="accessibility-dialog" aria-label="Preferencias de accesibilidad" bind:this={accessibilityDialog}>
	<div class="accessibility-dialog-actions">
		<h2>Accesibilidad</h2>
		<button aria-label="Cerrar accesibilidad" onclick={() => accessibilityDialog.close()}><span aria-hidden="true">×</span></button>
	</div>
	<DisplayPreferences embedded />
</dialog>
{/if}
