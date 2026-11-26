<script lang="ts">
	import { enhance } from '$app/forms';
	import logo from '$lib/assets/endosight-colon-real.svg';
	import artwork from '$lib/assets/login-reference.png';

	let { form } = $props();
	const demoEmail = 'demo@endosight.example';
	const demoPassword = 'EndoSight-Demo-2026!';
	let email = $state('');
	let password = $state('');
	let visible = $state(false);
	let busy = $state(false);

	const features = [
		['M13 2 4 14h7l-1 8 10-12h-7z', 'Análisis en tiempo real'],
		['M12 2v5m0 10v5M2 12h5m10 0h5M12 4a8 8 0 1 0 .01 0z', 'Detección y segmentación'],
		['M5 20v-5m7 5V9m7 11V4', 'Informes automáticos']
	];
</script>

{#snippet brand()}
	<div class="brand-lockup"><img src={logo} alt="" /><span>Endo<b>Sight</b></span></div>
{/snippet}
{#snippet icon(path: string)}
	<svg viewBox="0 0 24 24" aria-hidden="true"><path d={path} /></svg>
{/snippet}

<svelte:head><title>Iniciar sesión · EndoSight</title></svelte:head>

<main class="login">
	<aside class="showcase">
		{@render brand()}
		<h2>Detección asistida de <em>pólipos colorrectales</em></h2>
		<p>Plataforma con inteligencia artificial para el análisis de colonoscopías.</p>
		<ul>
			{#each features as [path, label] (label)}
				<li><span class="feature-icon">{@render icon(path)}</span>{label}</li>
			{/each}
		</ul>
		<div class="art" aria-hidden="true" style:background-image={'url(' + artwork + ')'}></div>
	</aside>

	<div class="access-area">
		<section class="access-card" aria-labelledby="login-title">
			{@render brand()}
			<h1 id="login-title">Iniciar sesión</h1>
			<p>Accede a la plataforma de análisis endoscópico.</p>
			<form method="POST" use:enhance={() => {
				busy = true;
				return async ({ update }) => {
					try { await update(); } finally { busy = false; }
				};
			}}>
				<label for="login-email">{@render icon('M3 5h18v14H3zM3 6l9 7 9-7')} Correo</label>
				<input id="login-email" required type="email" name="email" autocomplete="username" placeholder={demoEmail} bind:value={email} />
				<label for="login-password">{@render icon('M4 10h16v11H4zM8 10V6a4 4 0 0 1 8 0v4')} Contraseña</label>
				<div class="password-field">
					<input id="login-password" required type={visible ? 'text' : 'password'} name="password" autocomplete="current-password" placeholder="••••••••••••••••" bind:value={password} />
					<button type="button" class="eye" aria-label={visible ? 'Ocultar contraseña' : 'Mostrar contraseña'} onclick={() => (visible = !visible)}>
						{@render icon(visible ? 'M2 12s4-6 10-6 10 6 10 6-4 6-10 6-10-6-10-6zM12 9a3 3 0 1 0 .01 0z' : 'm3 3 18 18M9 6a12 12 0 0 1 13 6 15 15 0 0 1-3 4M6 7a16 16 0 0 0-4 5s4 6 10 6a10 10 0 0 0 4-1')}
					</button>
				</div>
				<label class="visibility"><input type="checkbox" bind:checked={visible} /> Mostrar contraseña</label>
				{#if form?.invalid}<p role="alert">Revisa el correo y la contraseña e inténtalo de nuevo.</p>{/if}
				<button class="submit" disabled={busy}>{@render icon('M12 3h8v18h-8M2 12h13m-5-5 5 5-5 5')} {busy ? 'Ingresando…' : 'Iniciar sesión'}</button>
			</form>
			<div class="separator" aria-hidden="true">o</div>
			<div class="demo">
				<div class="demo-heading">
					{@render icon('M8 2h8m-6 0v8L4 20a1 1 0 0 0 1 2h14a1 1 0 0 0 1-2l-6-10V2')}
					<div><h2>Cuenta de demostración</h2><p>Explora la plataforma con credenciales predefinidas.</p></div>
				</div>
				<div class="demo-controls">
					<div class="credentials"><span>{demoEmail}</span><span>{demoPassword}</span></div>
					<button type="button" onclick={() => { email = demoEmail; password = demoPassword; }}>Rellenar credenciales demo</button>
				</div>
			</div>
		</section>
	</div>
</main>

<style>
	.login { height: 100dvh; overflow: auto; display: grid; grid-template-columns: 41% minmax(0, 1fr); background: #edf3fc; color: #0b122f; font-size: clamp(1rem, 1.38vw, 1.375rem); }
	.showcase { position: relative; isolation: isolate; overflow: hidden; color: #fff; padding: 5.5vw 5vw 27vw 6.45vw; background: linear-gradient(65deg,#151956,#10285f 60%,#185db4); clip-path: ellipse(104% 165% at 0% 50%); }
	.showcase h2 { margin: 2.5rem 0 1rem; font-size: clamp(1.8rem,2.75vw,2.75rem); line-height: 1.12; }
	.showcase em { color: #81cdf5; font-style: normal; }
	.showcase p { color: inherit; }
	.showcase ul { list-style: none; padding: 0; margin: 2rem 0 0; display: grid; gap: .85rem; }
	.showcase li, .brand-lockup { display: flex; align-items: center; gap: .9rem; }
	.feature-icon { display:grid; place-items:center; width: 3.35rem; height: 3.15rem; border: 1px solid #4985cb; border-radius: .8rem; background: #234580; }
	svg { width: 1.3em; height: 1.3em; flex-shrink: 0; stroke: currentColor; fill: none; stroke-width: 1.7; stroke-linecap: round; stroke-linejoin: round; }
	.art { position: absolute; inset: auto 0 0; height: 25vw; z-index: -1; background-repeat: no-repeat; background-size: 244% auto; background-position: left bottom; mask-image: linear-gradient(transparent, #000 12%); }
	.access-area { display: grid; align-items: center; justify-items: center; padding: 4.9vw 6vw 3.3vw; min-width: 0; }
	.access-card { width: 100%; padding: 1.85vw 3.3vw 2vw; background: #fff; border: 1px solid #cbd8ed; border-radius: 2vw; box-shadow: 0 14px 28px #174caa1a; }
	.brand-lockup { font-size: clamp(1.6rem, 2.5vw, 2.5rem); font-weight: 800; }
	.brand-lockup img { width: clamp(2.5rem,4.3vw,4.3rem); height: auto; }
	.brand-lockup b { color: #1459d9; }
	.showcase .brand-lockup b { color: #54a7ff; }
	.access-card .brand-lockup { justify-content: center; margin-bottom: 1.25rem; }
	h1 { margin: 0; font-size: clamp(1.85rem,2.65vw,2.65rem); }
	p { margin: .35rem 0 0; color: #303e60; }
	form { margin-top: 1.85rem; }
	form label { display: flex; align-items: center; gap: .65rem; margin-bottom: .45rem; }
	form input:not([type='checkbox']) { width: 100%; background: #e8effc; border: 1px solid #9eafd0; border-radius: .65rem; min-height: 3.35rem; padding: .55rem 1.2rem; color: #0b122f; }
	label[for='login-password'] { margin-top: 1.2rem; }
	.password-field { position: relative; }
	.password-field input { padding-inline-end: 3.5rem !important; }
	.eye { position: absolute; inset: 0 .3rem 0 auto; border: 0; background: transparent; color: #0b122f; }
	.visibility { margin: .8rem 0 1.7rem; font-size: .9em; }
	.visibility input { width: 1.25em; height: 1.25em; }
	.submit { display: flex; justify-content: center; align-items: center; gap: .75rem; width: 100%; min-height: 3.7rem; color: #fff; background: linear-gradient(145deg,#235de4,#094aba); border: 0; border-radius: .85rem; font-size: 1.12em; font-weight: 700; }
	.separator { display: flex; align-items: center; gap: 1rem; margin: 1.45rem 0; }
	.separator::before,.separator::after { content: ''; height: 1px; flex: 1; background: #ccd7e9; }
	.demo { background: #e2ebfc; border-radius: 1rem; padding: .8rem 1.4rem 1rem; font-size: .83em; }
	.demo-heading { display: flex; gap: .8rem; align-items: center; }
	.demo-heading svg { color: #155dfc; width: 2rem; height: 2rem; }
	.demo h2 { font-size: 1.25em; margin: 0; }
	.demo-controls { display: grid; grid-template-columns: minmax(0,1fr) minmax(7rem,35%); gap: 1rem; align-items: center; margin-top: .75rem; }
	.credentials { display: grid; gap: .35rem; }
	.credentials span,.demo button { border: 1px solid #bdcce5; background: #f3f7ff; color: #0b122f; border-radius: .5rem; padding: .45rem .65rem; overflow-wrap: anywhere; }
	.demo button { border-color: #155dfc; font-weight: 600; }
	.login :focus-visible { outline: 3px solid #155dfc; outline-offset: 3px; }
	@media (max-width: 860px) {
		.login { display: block; }
		.showcase { display: none; }
		.access-area { min-height: 100%; padding: 1rem; }
		.access-card { max-width: 37rem; padding: clamp(1rem,5vw,2.5rem); border-radius: 1.25rem; }
	}
	@media (max-width: 420px) { .demo-controls { grid-template-columns: 1fr; gap: .5rem; } }
</style>
