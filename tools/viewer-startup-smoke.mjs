// Deterministic startup-failure contracts against the exact production package,
// without timing gates or a data service: the viewer still requires WebGPU
// (it is not on Stobie's AppHost and its WebGL2 fallback), and a failed worker
// start must fail startup and release the handle.
//
// node tools/viewer-startup-smoke.mjs PACKAGE_DIR
// PACKAGE_DIR is `stobie build-web --production` output, served by `stobie serve`.
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { once } from 'node:events';
import { createInterface } from 'node:readline';
import { chromium } from 'playwright';
import { assertGpuCompositing, hostedLinuxWebGpuLaunchOptions, uiLibraryEnvironment } from './browser-launch.mjs';

const directory = process.argv[2] || 'target/web-production';
const stobie = process.env.STOBIE || 'stobie';
const failureSpecs = {
  webgpu: {
    init: () => Object.defineProperty(navigator, 'gpu', { value: undefined }),
    phase: 'framework_start', cleanup: 'not_constructed', message: /WebGPU is unavailable/,
  },
  worker: { phase: 'worker', cleanup: 'destroyed', message: /./ },
};

const server = spawn(stobie, ['serve', directory, '--port', '0', '--json'], { stdio: ['ignore', 'pipe', 'inherit'] });
const [line] = await once(createInterface({ input: server.stdout }), 'line');
const base = `${JSON.parse(line).url}emuella-viewer/`;
const browser = await chromium.launch({ ...hostedLinuxWebGpuLaunchOptions(), env: uiLibraryEnvironment() });
try {
  const session = await browser.newBrowserCDPSession();
  assertGpuCompositing((await session.send('SystemInfo.getInfo')).gpu);
  await session.detach();
  for (const [failure, spec] of Object.entries(failureSpecs)) {
    const context = await browser.newContext();
    if (failure === 'worker') await context.route('**/worker.js', route => route.abort());
    if (spec.init) await context.addInitScript(spec.init);
    const page = await context.newPage();
    await page.goto(base);
    await page.waitForFunction(() => window.__STOBIE_STARTUP?.status === 'failed', null, { timeout: 60000 });
    await page.waitForFunction(() => window.__STOBIE_STARTUP.cleanup, null, { timeout: 5000 });
    const result = await page.evaluate(() => ({ startup: window.__STOBIE_STARTUP, text: document.getElementById('loading').textContent, ready: document.body.classList.contains('ready') }));
    assert(result.startup.failure.phase.includes(spec.phase), JSON.stringify(result));
    assert.match(result.startup.failure.message, spec.message);
    assert(result.text.includes('Initialisation failed'));
    assert.equal(result.ready, false);
    assert.equal(result.startup.cleanup, spec.cleanup, 'failed startup must release its handle');
    await context.close();
    console.log(`Startup failure handled: emuella-viewer/${failure}`);
  }
} finally {
  await browser.close();
  server.kill();
}
