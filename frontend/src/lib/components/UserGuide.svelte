<script lang="ts">
	import { resolve } from '$app/paths';
</script>

<div class="page-heading">
	<div>
		<h1>Ayuda</h1>
		<p class="muted">Una guía breve para preparar y revisar la asistencia visual.</p>
	</div>
</div>
<div class="guide-content">
	<section class="experimental-note" aria-labelledby="scope-title">
		<h2 id="scope-title">Prototipo experimental</h2>
		<p>
			Esta plataforma ofrece apoyo a la visualización de video endoscópico con anotaciones
			experimentales. No reemplaza el criterio clínico ni proporciona un diagnóstico autónomo.
		</p>
	</section>
	<section class="panel" aria-labelledby="quick-start">
		<h2 id="quick-start">Guía rápida</h2>
		<ol class="help-steps">
			<li>
				<strong>Crea o abre una sesión.</strong> Entra en
				<a class="text-link" href={resolve('/sessions/new')}>Nueva sesión</a>
				para preparar una fuente. En <a class="text-link" href={resolve('/sessions')}>Sesiones</a> puedes
				abrir el detalle de las sesiones de esta pestaña; el detalle no reinicia la transmisión.
			</li>
			<li>
				<strong>Elige cámara o video.</strong> Usa Capturadora para una cámara o dispositivo de captura;
				usa Archivo para seleccionar un video autorizado. El archivo se reproduce en bucle.
			</li>
			<li>
				<strong>Prepara la fuente.</strong> Pulsa Previsualizar, concede el permiso de cámara cuando corresponda
				y confirma que la imagen se mueve y corresponde a la fuente elegida.
			</li>
			<li>
				<strong>Inicia la asistencia.</strong> Pulsa Iniciar asistencia y espera a que el estado indique
				Conectado.
			</li>
			<li>
				<strong>Revisa conexión y anotaciones.</strong> El encabezado indica Video original o Video con
				anotaciones. Alterna con Mostrar original / Mostrar anotaciones. Estar conectado no garantiza
				que haya anotaciones; su ausencia no descarta una lesión.
			</li>
			<li>
				<strong>Detén o finaliza.</strong> Detener asistencia interrumpe el procesamiento y mantiene la
				fuente original disponible. Reintentar asistencia vuelve a conectar. Finalizar sesión cierra la
				fuente y abre el detalle.
			</li>
		</ol>
	</section>
	<section class="panel" aria-labelledby="requirements">
		<h2 id="requirements">Antes de empezar</h2>
		<ul class="guide-list">
			<li>
				Usa un navegador con soporte de WebRTC y acceso a cámara. Para archivos, también debe poder
				reproducir el formato y capturar el video desde canvas.
			</li>
			<li>
				Conecta la cámara o capturadora y autoriza su acceso en el navegador y en el sistema
				operativo.
			</li>
			<li>Fuera de localhost, el acceso a cámara requiere HTTPS.</li>
			<li>La asistencia necesita conexión con el servicio de procesamiento.</li>
		</ul>
		<p>
			Adapta tema, contraste, texto y paleta en <a class="text-link" href={resolve('/settings')}
				>Configuración visual</a
			>.
		</p>
	</section>
	<section class="panel" aria-labelledby="troubleshooting">
		<h2 id="troubleshooting">Solución de problemas</h2>
		<dl class="troubleshooting">
			<dt>Sin conexión</dt>
			<dd>
				Lee el mensaje de estado. Comprueba la red y que el servicio de procesamiento esté
				disponible. Si la fuente sigue lista, pulsa Reintentar asistencia. Consulta la imagen
				original si la anotada parece detenida.
			</dd>
			<dt>Fuente no disponible</dt>
			<dd>
				Revisa permisos, conexión del dispositivo y si otra aplicación lo está usando. En la
				preparación, pulsa Actualizar dispositivos y Previsualizar. Para un archivo, comprueba que
				el navegador pueda reproducirlo. Si la fuente se desconectó durante la sesión, finaliza y
				prepara una nueva.
			</dd>
			<dt>Video sin anotaciones</dt>
			<dd>
				Confirma que figura Conectado y que estás mostrando Video con anotaciones. Revisa los
				mensajes de error. La ausencia de marcas no es un resultado clínico negativo.
			</dd>
			<dt>Asistencia detenida</dt>
			<dd>
				La fuente original puede seguir visible sin procesamiento. Si deseas continuar y la fuente
				está disponible, pulsa Reintentar asistencia; para cerrar la fuente, pulsa Finalizar sesión.
			</dd>
		</dl>
	</section>
	<section class="panel" aria-labelledby="privacy">
		<h2 id="privacy">Privacidad y manejo de video</h2>
		<p>
			Al iniciar la asistencia, el frontend transmite video al servicio de procesamiento mediante
			WebRTC y muestra el video devuelto. La cámara se solicita sin audio. El frontend no implementa
			grabación de video; al finalizar, cierra la conexión y libera la fuente.
		</p>
		<p>
			Los datos de las sesiones se mantienen en memoria de la pestaña y se pierden al recargar. Solo
			las preferencias visuales se guardan en localStorage. Esto no establece cómo el servidor
			conserva o maneja datos: el frontend no permite verificarlo.
		</p>
		<p class="muted">Usa únicamente fuentes de video autorizadas para esta prueba experimental.</p>
	</section>
	<div class="actions">
		<a class="button primary" href={resolve('/sessions/new')}>Nueva sesión</a><a
			class="button"
			href={resolve('/settings')}>Configuración</a
		>
	</div>
</div>
