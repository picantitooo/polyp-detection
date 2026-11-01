<script lang="ts">
	let { title, description, features }: { title: string; description: string; features: string[] } =
		$props();
</script>

<svelte:head><title>{title} · Polyp</title></svelte:head>
<div class="page-heading"><h1>{title}</h1></div>
<section class="placeholder">
	<h2>Pendiente de implementar</h2>
	<p class="muted">{description}</p>
	<ul>
		{#each features as feature (feature)}<li>{feature}</li>{/each}
	</ul>
</section>
