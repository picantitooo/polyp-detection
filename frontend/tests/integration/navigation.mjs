// Browser smoke test with a fake camera and a WebRTC loopback peer.
// This verifies UI, transport lifecycle and cleanup, NOT medical inference.
import assert from 'node:assert/strict';
import { chromium } from 'playwright';
const browser = await chromium.launch({
	executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH || undefined,
	args: ['--use-fake-device-for-media-stream', '--use-fake-ui-for-media-stream']
});
try {
	const context = await browser.newContext({
		permissions: ['camera'],
		viewport: { width: 1440, height: 1000 }
	});
	const page = await context.newPage();
	const errors = [];
	page.on('pageerror', (error) => errors.push(error.message));
	await page.addInitScript(() => {
		window.testStreams = [];
		const original = navigator.mediaDevices.getUserMedia.bind(navigator.mediaDevices);
		navigator.mediaDevices.getUserMedia = async (constraints) => {
			const stream = await original(constraints);
			window.testStreams.push(stream);
			return stream;
		};
	});
	await page.route('**/webrtc/offer', async (route) => {
		const headers = {
			'Access-Control-Allow-Origin': '*',
			'Access-Control-Allow-Headers': 'content-type'
		};
		if (route.request().method() === 'OPTIONS') {
			await route.fulfill({ status: 204, headers });
			return;
		}
		const offer = route.request().postDataJSON();
		const answer = await page.evaluate(async (description) => {
			const pc = new RTCPeerConnection({ iceServers: [] });
			window.testPeer = pc;
			pc.ontrack = (event) => pc.addTrack(event.track, new MediaStream([event.track]));
			await pc.setRemoteDescription(description);
			await pc.setLocalDescription(await pc.createAnswer());
			if (pc.iceGatheringState !== 'complete')
				await new Promise((resolve) =>
					pc.addEventListener('icegatheringstatechange', () => {
						if (pc.iceGatheringState === 'complete') resolve();
					})
				);
			return { sdp: pc.localDescription.sdp, type: pc.localDescription.type };
		}, offer);
		await route.fulfill({
			status: 200,
			headers,
			contentType: 'application/json',
			body: JSON.stringify(answer)
		});
	});
	await page.goto(process.env.TEST_BASE_URL || 'http://127.0.0.1:5173');
	await page.getByRole('heading', { name: 'Inicio' }).waitFor();
	for (const label of ['Hallazgos', 'Evidencia', 'Informes', 'Modelos', 'Configuración']) {
		await page
			.getByRole('navigation', {
				name: label === 'Configuración' ? 'Aplicación' : 'Principal',
				exact: true
			})
			.getByRole('link', { name: new RegExp(label) })
			.click();
		await page
			.getByRole('heading', { name: label === 'Modelos' ? 'Modelos de IA' : label, exact: true })
			.waitFor();
		await page.getByText('Pendiente de implementar').waitFor();
	}
	await page.getByRole('link', { name: 'Sesiones', exact: true }).click();
	await page.getByRole('link', { name: 'Nueva sesión', exact: false }).first().click();
	assert.equal(await page.getByRole('button', { name: 'Iniciar asistencia' }).isDisabled(), true);
	await page.getByRole('button', { name: 'Previsualizar' }).click();
	await page.waitForFunction(
		() => document.querySelector('video[aria-label="Fuente de video original"]')?.videoWidth > 0
	);
	await page.getByRole('button', { name: 'Iniciar asistencia' }).click();
	await page.waitForURL('**/live');
	await page.getByText('Conectado', { exact: true }).waitFor();
	assert.equal(await page.locator('.sidebar').isVisible(), false);
	await page.getByRole('button', { name: 'Mostrar original', exact: true }).click();
	await page.getByRole('heading', { name: 'Video original', exact: true }).waitFor();
	await page.getByRole('button', { name: 'Detener asistencia', exact: true }).click();
	assert.equal(
		await page.evaluate(() => window.testStreams[0].getVideoTracks()[0].readyState),
		'live'
	);
	await page.getByRole('button', { name: 'Finalizar sesión', exact: true }).click();
	await page.getByRole('heading', { name: 'Detalle de sesión' }).waitFor();
	assert.equal(
		await page.evaluate(() =>
			window.testStreams.every((s) => s.getTracks().every((t) => t.readyState === 'ended'))
		),
		true
	);
	await page.getByRole('button', { name: 'Evidencia', exact: true }).click();
	await page.getByRole('heading', { name: 'Evidencia', exact: true }).waitFor();
	await page.reload();
	await page.getByRole('heading', { name: 'Sesión no disponible' }).waitFor();
	await page.setViewportSize({ width: 360, height: 800 });
	await page.getByRole('link', { name: 'Volver a sesiones' }).click();
	assert.equal(
		await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth),
		true
	);
	assert.deepEqual(errors, []);
	console.log(
		'PASS: placeholders, source preview, WebRTC loopback, stop/finish cleanup, reload and mobile layout.'
	);
	console.log(
		'NOTE: camera and backend are simulated. ONNX inference must be checked on the target machine.'
	);
} finally {
	await browser.close();
}
