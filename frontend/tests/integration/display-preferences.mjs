import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const browser = await chromium.launch({
	executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH || undefined
});
const base = process.env.TEST_BASE_URL || 'http://127.0.0.1:5173';
try {
	const context = await browser.newContext({
		viewport: { width: 1366, height: 768 },
		colorScheme: 'dark'
	});
	const page = await context.newPage();
	const errors = [];
	page.on('pageerror', (error) => errors.push(error.message));
	await page.goto(`${base}/settings`);
	const theme = page.getByLabel('Tema', { exact: true });
	await theme.waitFor();
	await page.waitForFunction(() => document.documentElement.dataset.colorScheme === 'dark');
	await theme.selectOption('light');
	await page.getByLabel('Contraste', { exact: true }).selectOption('high');
	await page.getByLabel('Tamaño de texto').selectOption('extra-large');
	await page.getByLabel('Paleta de la interfaz').selectOption('tritanopia');
	await page.getByLabel('Reducir animaciones', { exact: false }).check();
	await page.reload();
	await page.waitForFunction(() => document.documentElement.dataset.textSize === 'extra-large');
	assert.equal(await theme.inputValue(), 'light');
	assert.equal(await page.getByLabel('Contraste', { exact: true }).inputValue(), 'high');
	assert.equal(await page.getByLabel('Paleta de la interfaz').inputValue(), 'tritanopia');
	assert.equal(await page.getByLabel('Reducir animaciones', { exact: false }).isChecked(), true);
	assert.equal(
		await page.evaluate(() => getComputedStyle(document.documentElement).fontSize),
		'18px'
	);
	await theme.focus();
	assert.equal(await theme.evaluate((el) => el.matches(':focus-visible')), true);
	for (const scheme of ['light', 'dark']) {
		await theme.selectOption(scheme);
		for (const palette of ['standard', 'red-green', 'tritanopia']) {
			await page.getByLabel('Paleta de la interfaz').selectOption(palette);
			for (const contrast of ['normal', 'high']) {
				await page.getByLabel('Contraste', { exact: true }).selectOption(contrast);
				const ratios = await page.evaluate(() => {
					function luminance(color) {
						const rgb = color
							.match(/[\d.]+/g)
							.slice(0, 3)
							.map(Number)
							.map((v) => {
								v /= 255;
								return v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4;
							});
						return rgb[0] * 0.2126 + rgb[1] * 0.7152 + rgb[2] * 0.0722;
					}
					const surface = getComputedStyle(document.querySelector('.panel')).backgroundColor;
					return [
						'.panel h2',
						'.panel .muted',
						'.sidebar nav a.current',
						'.text-link',
						'.panel button',
						'.panel select'
					].map((selector) => {
						const el = document.querySelector(selector);
						if (!el) return 21;
						const style = getComputedStyle(el);
						const bg =
							style.backgroundColor === 'rgba(0, 0, 0, 0)' ? surface : style.backgroundColor;
						const values = [luminance(style.color), luminance(bg)].sort((a, b) => b - a);
						return (values[0] + 0.05) / (values[1] + 0.05);
					});
				});
				assert.ok(
					ratios.every((ratio) => ratio >= 4.5),
					`${scheme}/${palette}/${contrast}: ${ratios}`
				);
			}
		}
	}
	for (const width of [1366, 768, 360]) {
		await page.setViewportSize({ width, height: 800 });
		for (const path of ['/settings', '/help', '/']) {
			await page.goto(`${base}${path}`);
			await page.waitForFunction(() => document.documentElement.dataset.textSize === 'extra-large');
			assert.ok(
				await page.evaluate(
					() =>
						document.documentElement.scrollWidth <= innerWidth &&
						document.querySelector('main').scrollWidth <= document.querySelector('main').clientWidth
				),
				`Overflow at ${path}, ${width}`
			);
		}
	}
	assert.equal(await page.getByRole('heading', { name: 'Sesiones recientes' }).count(), 0);
	assert.ok(
		(
			await page.getByRole('link', { name: 'Nueva sesión', exact: true }).getAttribute('href')
		).endsWith('/sessions/new')
	);
	await page.goto(`${base}/settings`);
	await page.getByRole('button', { name: 'Restablecer preferencias' }).click();
	await page.getByRole('status').filter({ hasText: 'Preferencias restablecidas' }).waitFor();
	assert.equal(await theme.inputValue(), 'system');
	assert.equal(await page.getByLabel('Contraste', { exact: true }).inputValue(), 'normal');
	assert.equal(await page.getByLabel('Tamaño de texto').inputValue(), 'normal');
	assert.equal(await page.getByLabel('Paleta de la interfaz').inputValue(), 'standard');
	assert.equal(await page.getByLabel('Reducir animaciones', { exact: false }).isChecked(), false);
	await page.emulateMedia({ colorScheme: 'light' });
	await page.waitForFunction(() => document.documentElement.dataset.colorScheme === 'light');
	await page.evaluate(() =>
		localStorage.setItem('polyp.display-preferences.v1', '{"theme":"unknown","textSize":42}')
	);
	await page.reload();
	await page.waitForFunction(() => document.documentElement.dataset.theme === 'system');
	assert.equal(await theme.inputValue(), 'system');
	const blocked = await browser.newContext();
	await blocked.addInitScript(() => {
		Object.defineProperty(window, 'localStorage', {
			get() {
				throw new Error('Storage blocked');
			}
		});
	});
	const blockedPage = await blocked.newPage();
	await blockedPage.goto(`${base}/settings`);
	await blockedPage
		.getByText('El almacenamiento local no está disponible.', { exact: false })
		.waitFor();
	await blockedPage.getByLabel('Tema', { exact: true }).selectOption('dark');
	await blockedPage.waitForFunction(() => document.documentElement.dataset.colorScheme === 'dark');
	assert.deepEqual(errors, []);
	console.log(
		'PASS: persisted preferences, reset, system theme, keyboard focus, palette contrast, responsive routes, invalid and blocked storage.'
	);
} finally {
	await browser.close();
}
