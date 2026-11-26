<script lang="ts">
	import { resolve } from '$app/paths';
	let query = $state('');
	let category = $state('all');
	let showAll = $state(false);
	const topics = [
		{ id: 'start', title: 'Primeros pasos', description: 'Prepara e inicia una sesión', icon: 'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18Zm-2 5 6 4-6 4z' },
		{ id: 'video', title: 'Video y cámara', description: 'Conecta y configura tu fuente', icon: 'M3 5h13v14H3zM16 10l5-3v10l-5-3' },
		{ id: 'trouble', title: 'Solucionar problemas', description: 'Resuelve errores comunes', icon: 'M14 6a5 5 0 0 0-6 6L3 17a2 2 0 0 0 3 3l5-5a5 5 0 0 0 6-6l-3 3-3-3z' },
		{ id: 'privacy', title: 'Privacidad', description: 'Uso y manejo del video', icon: 'M12 2 4 5v6c0 5 3 8 8 11 5-3 8-6 8-11V5zM8 12l3 3 5-6' }
	];
	const questions = [
		{ category: 'start', question: '¿Cómo inicio una sesión?', answer: 'Abre Nueva sesión, selecciona una cámara o archivo autorizado y pulsa Previsualizar. Comprueba la imagen, inicia la asistencia y espera el estado Conectado.' },
		{ category: 'start', question: '¿Cómo finalizo o detengo la asistencia?', answer: 'Detener asistencia cierra la conexión y mantiene la fuente original. Reintentar vuelve a conectar. Finalizar sesión libera la fuente y abre el detalle.' },
		{ category: 'video', question: '¿Qué fuente de video puedo usar?', answer: 'Usa Capturadora para una cámara o dispositivo de captura, o Archivo para un video autorizado. El archivo se reproduce en bucle. El navegador debe poder reproducirlo y capturarlo desde canvas.' },
		{ category: 'video', question: '¿Qué permisos necesita la cámara?', answer: 'Autoriza la cámara en el navegador y el sistema operativo. Fuera de localhost se requiere HTTPS. La cámara se solicita sin audio.' },
		{ category: 'trouble', question: '¿Qué hago si falla la cámara o el archivo?', answer: 'Comprueba los permisos, la conexión y si otra aplicación usa la cámara. Pulsa Actualizar dispositivos y Previsualizar. Para archivos, comprueba que el navegador soporte el formato.' },
		{ category: 'trouble', question: '¿Por qué no aparecen anotaciones?', answer: 'Confirma el estado Conectado y selecciona Mostrar anotaciones. Revisa la conexión y los mensajes. La ausencia de marcas no descarta una lesión.' },
		{ category: 'trouble', question: '¿Qué hago si se interrumpe la conexión?', answer: 'Comprueba la red y el servicio de procesamiento. Si la fuente sigue disponible, pulsa Reintentar asistencia y consulta la imagen original si la anotada se detiene.' },
		{ category: 'privacy', question: '¿Dónde se guardan mis hallazgos?', answer: 'El historial, los recortes y las revisiones se guardan en este navegador. Evidencia permite consultar recortes y Hallazgos permite agruparlos y registrar una revisión.' },
		{ category: 'privacy', question: '¿Cómo se maneja el video?', answer: 'Durante la asistencia el video se transmite por WebRTC al servicio de procesamiento. La interfaz no graba el video. Al finalizar, cierra la conexión y libera la fuente.' },
		{ category: 'privacy', question: '¿Cuál es el alcance de la asistencia?', answer: 'Es un prototipo experimental de apoyo visual. Las anotaciones no constituyen un diagnóstico autónomo y no sustituyen el criterio del especialista.' }
	];
	let matching = $derived(questions.filter((item) => (category === 'all' || item.category === category) && (item.question + ' ' + item.answer).toLocaleLowerCase().includes(query.trim().toLocaleLowerCase())));
	let visible = $derived(category === 'all' && !query && !showAll ? matching.filter((item) => ['¿Cómo inicio una sesión?', '¿Por qué no aparecen anotaciones?', '¿Qué hago si falla la cámara o el archivo?', '¿Dónde se guardan mis hallazgos?'].includes(item.question)) : matching);
</script>

<svelte:head><title>Centro de ayuda · EndoSight</title></svelte:head>
<div class="support-page">
	<header class="support-page-header"><p class="support-kicker">RECURSOS</p><h1>Centro de ayuda</h1><p>Encuentra respuestas para utilizar EndoSight.</p></header>
	<label class="support-search"><span class="visually-hidden">Buscar en ayuda</span><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 4 4"/></svg><input type="search" placeholder="Buscar en ayuda…" bind:value={query}/></label>
	<nav class="support-topics" aria-label="Temas de ayuda">
		{#each topics as topic (topic.id)}
			<button class:active={category === topic.id} aria-pressed={category === topic.id} onclick={() => (category = category === topic.id ? 'all' : topic.id)}>
				<span class="support-topic-icon"><svg viewBox="0 0 24 24" aria-hidden="true"><path d={topic.icon}/></svg></span><span><strong>{topic.title}</strong><small>{topic.description}</small></span><span aria-hidden="true" class="support-chevron">›</span>
			</button>
		{/each}
	</nav>
	<div class="support-section-heading"><h2>Preguntas frecuentes</h2><button class="text-button" onclick={() => { const reset = category !== 'all' || !!query; category = 'all'; query = ''; showAll = reset ? true : !showAll; }}>{showAll && category === 'all' && !query ? 'Ver principales' : 'Ver todas'}</button></div>
	<section class="support-faq" aria-label="Preguntas frecuentes">
		{#each visible as item (item.question)}<details><summary><span>{item.question}</span><svg viewBox="0 0 24 24" aria-hidden="true"><path d="m7 10 5 5 5-5"/></svg></summary><p>{item.answer}</p></details>
		{:else}<p class="support-no-results" role="status">No encontramos resultados. Prueba con otras palabras o cambia el tema.</p>{/each}
	</section>
	<nav class="actions" aria-label="Acciones de ayuda"><a class="button" href={resolve('/sessions/new')}>Preparar fuente e iniciar asistencia</a><a class="button" href={resolve('/evidence')}>Revisar evidencia</a><a class="button" href={resolve('/reports')}>Consultar informes</a></nav>
	<aside class="support-diagnostic"><div><strong>¿Necesitas revisar tu equipo?</strong><p>Comprueba la fuente y la conexión con el procesador.</p></div><a class="button" href={resolve('/settings')}>Diagnóstico de la estación →</a></aside>
</div>
