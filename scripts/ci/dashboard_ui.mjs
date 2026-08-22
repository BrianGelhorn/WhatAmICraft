#!/usr/bin/env node
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import http from 'node:http';
import path from 'node:path';
import {openBrowser} from '@remotion/renderer';

const root = path.resolve(import.meta.dirname, '../..');
const index = await readFile(path.join(root, 'dashboard/index.html'));
const requests = [];
let failNext = null;
let diagnosticsReads = 0;

const episode = (id, target, overrides = {}) => ({
  id,
  target,
  kind: 'Item',
  format: 'clues',
  formatLabel: 'Quiz definitivo',
  clues: 3,
  needsReview: false,
  hasVideo: false,
  hasLegacyVideo: false,
  hasThumbnail: false,
  hasThumbnails: false,
  videoUrl: null,
  thumbnailUrl: null,
  thumbnailUrls: {},
  status: 'Sin generar',
  queueStatus: null,
  platforms: [],
  answer: target,
  clueDetails: [],
  revealText: '',
  ...overrides,
});

const preview = {
  hasVideo: true,
  hasThumbnail: true,
  hasThumbnails: true,
  videoUrl: 'data:video/mp4;base64,AAAA',
  thumbnailUrl: 'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw==',
  thumbnailUrls: {vertical: 'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw=='},
  answer: 'Wind Charge',
  clueDetails: [
    {number: 1, text: 'First clue', voiceText: 'First clue', voiceUrl: null},
    {number: 2, text: 'Second clue', voiceText: 'Second clue', voiceUrl: null},
    {number: 3, text: 'Third clue', voiceText: 'Third clue', voiceUrl: null},
  ],
  revealText: 'It is the Wind Charge!',
};

const state = {
  episodes: [
    episode('mc-01', 'Crossbow'),
    episode('mc-02', 'Wind Charge', {...preview, status: 'Esperando aprobación'}),
    episode('mc-03', 'Recovery Compass', {...preview, status: 'En cola', queueStatus: 'pending'}),
    episode('mc-04', 'Golden Apple', {...preview, kind: 'Food', status: 'Publicado', platforms: ['youtube']}),
  ],
  formats: [{id: 'clues', label: 'Quiz definitivo', enabled: true, priority: 5, sharePct: 100, targetStock: 8, total: 4, rendered: 3, stock: 2, review: 1, queued: 1}],
  music: {
    originals: [{filename: 'Cat.ogg', title: 'Cat', starts: [12]}],
    tracks: [{id: 'track-1', title: 'Fixture song', channel: 'Fixture', durationSeconds: 180, url: 'https://youtu.be/fixture', clips: [{id: 'clip-1', templateId: 'clues', templateLabel: 'Quiz definitivo', startSeconds: 12, durationSeconds: 120, audioUrl: 'data:audio/mp4;base64,AAAA'}]}],
  },
  analytics: {
    schemaVersion: 1,
    generatedAt: '2026-08-21T12:00:00Z',
    summary: {videos: 1, views: 100, engagements: 12, engagementRateByViews: 12},
    platforms: [{platform: 'youtube', videos: 1, views: 100, engagements: 12, error: null, syncedAt: '2026-08-21T12:00:00Z'}],
    series: [{platform: 'youtube', capturedAt: '2026-08-21T12:00:00Z', views: 100, engagements: 12}],
    cohorts: [{dimension: 'formatLabel', platform: 'youtube', value: 'Quiz definitivo', videos: 1, measuredVideos: 1, viewsPerVideo: 100, lifetimeViewsPerHour: 10, engagementRateByViews: 12, completionRate: 70}],
    quality: [{platform: 'youtube', videos: 1, measuredVideos: 1, reachPerView: 0.9, averageWatchSeconds: 18, completionRate: 70, coveragePercent: 100, warnings: []}],
    trends: [{platform: 'youtube', trend: 'up', viewsPerHour: 10}],
    alerts: [{platform: 'youtube', severity: 'low', message: 'Fixture alert'}],
    recommendations: [{platform: 'youtube', action: 'Fixture recommendation', reason: 'Fixture evidence'}],
    videos: [{platform: 'youtube', episodeId: 'mc-04', target: 'Golden Apple', formatLabel: 'Quiz definitivo', views: 100, reach: 90, viewsPerHourSincePrevious: 10, engagementRateByViews: 12, likes: 8, comments: 2, shares: 1, saves: 1, averageWatchSeconds: 18, completionRate: 70}],
    observations: ['Fixture observation'],
  },
  job: {status: 'failed', label: 'Generación fallida', source: 'manual', lines: ['fixture error'], returnCode: 1, updatedAt: '2026-08-21T12:00:00Z'},
  publishing: {
    config: {
      title: 'Guess the {kind}',
      caption: 'Fixture caption',
      hashtags: ['minecraft', 'quiz'],
      schedule: {enabled: true, intervalMinutes: 720},
      generation: {enabled: true, intervalMinutes: 180, targetStock: 8, lowStockThreshold: 5, publishGuardMinutes: 30, formats: {clues: {enabled: true, priority: 5}}},
      platforms: {
        youtube: {enabled: true, privacyStatus: 'private', categoryId: '20', title: 'YouTube {kind}', caption: 'YouTube fixture'},
        tiktok: {enabled: true, privacyLevel: 'SELF_ONLY', isAigc: false, disableComment: false, title: 'TikTok {kind}', caption: 'TikTok fixture'},
        instagram: {enabled: true, shareToFeed: true, publicVideoBaseUrl: 'https://example.invalid', title: 'Instagram {kind}', caption: 'Instagram fixture'},
        facebook: {enabled: true, videoState: 'DRAFT', title: 'Facebook {kind}', caption: 'Facebook fixture'},
      },
    },
    credentials: {youtube: true, tiktok: true, instagram: true, facebook: true},
    nextRunAt: '2026-08-22T12:00:00Z',
    nextGenerationAt: '2026-08-21T15:00:00Z',
    lastError: null,
    tiktokAccount: {connected: true, displayName: 'Fixture account'},
    tiktokRedirectUri: 'https://example.invalid/tiktok',
    youtubeRedirectUri: 'https://example.invalid/youtube',
  },
};

const diagnostics = {
  checkedAt: '2026-08-21T12:00:00Z',
  internet: true,
  database: {exists: true, sizeKb: 64},
  disk: {freeGb: 40, usedPct: 50},
  counts: {videos: 3, episodes: 4, pending: 1, candidates: 1, failed: 0, published: 1},
  access: {dashboard: 'https://example.invalid/dashboard', publicVideos: 'https://example.invalid/videos'},
  ops: {backups: 1, latestBackup: '2026-08-21T10:00:00Z', contextUpdated: '2026-08-21T11:00:00Z'},
  services: [{name: 'dashboard', state: 'running', status: 'responding'}, {name: 'analytics-api', state: 'external', status: 'configured'}],
  errors: [],
  logs: [],
};

const json = (response, value, status = 200) => {
  const body = Buffer.from(JSON.stringify(value));
  response.writeHead(status, {'Content-Type': 'application/json; charset=utf-8', 'Content-Length': body.length});
  response.end(body);
};

const server = http.createServer(async (request, response) => {
  const url = new URL(request.url, 'http://127.0.0.1');
  if (request.method === 'GET' && url.pathname === '/') {
    response.writeHead(200, {'Content-Type': 'text/html; charset=utf-8', 'Content-Length': index.length});
    response.end(index);
    return;
  }
  if (request.method === 'GET' && url.pathname === '/favicon.ico') {
    response.writeHead(204);
    response.end();
    return;
  }
  if (request.method === 'GET' && url.pathname === '/api/state') return json(response, state);
  if (request.method === 'GET' && url.pathname === '/api/diagnostics') {
    diagnosticsReads += 1;
    return json(response, diagnostics);
  }
  if (request.method === 'GET' && url.pathname.startsWith('/api/analytics/export.')) {
    response.writeHead(200, {'Content-Type': 'text/plain'});
    response.end('fixture export');
    return;
  }
  if (request.method !== 'POST') return json(response, {ok: false, error: 'not found'}, 404);

  const chunks = [];
  for await (const chunk of request) chunks.push(chunk);
  const body = chunks.length ? JSON.parse(Buffer.concat(chunks)) : {};
  requests.push({path: url.pathname, body});
  if (failNext === url.pathname) {
    failNext = null;
    return json(response, {ok: false, error: 'Fallo controlado'});
  }

  if (url.pathname === '/api/generate') state.job = {status: 'running', label: 'Generando fixture', source: 'manual', lines: ['started'], returnCode: null};
  if (url.pathname === '/api/job/cancel') state.job = {status: 'cancelled', label: 'Generación cancelada', source: 'manual', lines: ['cancelled'], returnCode: -15};
  if (url.pathname === '/api/action') {
    const item = state.episodes.find((value) => value.id === body.episodeId);
    if (body.action === 'approve') Object.assign(item, {queueStatus: 'pending', status: 'En cola'});
    if (body.action === 'unqueue') Object.assign(item, {queueStatus: null, status: 'Esperando aprobación'});
    if (body.action === 'hints') Object.assign(item, {needsReview: true, status: 'Pistas pendientes'});
    if (body.action === 'clear-hints') Object.assign(item, {needsReview: false, status: 'Esperando aprobación'});
    if (body.action === 'reject') state.episodes = state.episodes.filter((value) => value.id !== body.episodeId);
  }
  if (url.pathname === '/api/publishing/config') state.publishing.config = body.config;
  if (url.pathname === '/api/tiktok/disconnect') state.publishing.tiktokAccount = {connected: false, displayName: ''};
  if (url.pathname === '/api/music/delete') state.music.tracks = state.music.tracks.filter((track) => track.id !== body.trackId);
  return json(response, {ok: true});
});

await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
const base = `http://127.0.0.1:${server.address().port}`;
const browserErrors = [];
let browser;

const waitNode = async (description, predicate, timeout = 5000) => {
  const deadline = Date.now() + timeout;
  while (Date.now() < deadline) {
    if (predicate()) return;
    await new Promise((resolve) => setTimeout(resolve, 40));
  }
  throw new Error(`Timeout: ${description}`);
};

try {
  browser = await openBrowser('chrome', {
    browserExecutable: process.env.DASHBOARD_BROWSER_EXECUTABLE || null,
    chromiumOptions: {headless: true, gl: 'swiftshader'},
    logLevel: 'error',
  });
  const page = await browser.newPage({
    context: () => null,
    logLevel: 'error',
    indent: false,
    pageIndex: 0,
    onBrowserLog: (entry) => {
      if (entry.type === 'error' || entry.type === 'warning') browserErrors.push(entry.text);
    },
    onLog: () => undefined,
  });
  page.on('error', (error) => browserErrors.push(error.message));
  await page.evaluateOnNewDocument(() => { window.confirm = () => true; });
  await page.goto({url: base, timeout: 15000});

  const evaluate = (fn, ...args) => page.evaluate(fn, ...args);
  const waitPage = async (description, predicate, timeout = 5000) => {
    const deadline = Date.now() + timeout;
    while (Date.now() < deadline) {
      if (await evaluate(predicate)) return;
      await new Promise((resolve) => setTimeout(resolve, 40));
    }
    throw new Error(`Timeout: ${description}`);
  };
  const click = async (selector) => evaluate((value) => {
    const element = document.querySelector(value);
    if (!element) throw new Error(`Missing element: ${value}`);
    element.click();
  }, selector);
  const setValue = async (selector, value, event = 'input') => evaluate((target, next, eventName) => {
    const element = document.querySelector(target);
    element.value = next;
    element.dispatchEvent(new Event(eventName, {bubbles: true}));
  }, selector, value, event);
  const requestCount = (pathName) => requests.filter((item) => item.path === pathName).length;
  const clickRequest = async (selector, pathName) => {
    const before = requestCount(pathName);
    await click(selector);
    await waitNode(pathName, () => requestCount(pathName) > before);
    await new Promise((resolve) => setTimeout(resolve, 100));
  };

  await waitPage('initial dashboard state', () => document.querySelector('#video-result-count')?.textContent !== '0 resultados');
  assert.deepEqual(await evaluate(() => [...document.querySelectorAll('.section-nav [data-view]')].map((button) => button.textContent.trim())), ['Operación', 'Música', 'Rendimiento', 'Automatización', 'Sistema']);
  for (const view of ['music', 'analytics', 'publishing', 'system', 'home']) {
    await click(`[data-view="${view}"]`);
    assert.equal(await evaluate((name) => !document.querySelector(`[data-view-panel="${name}"]`).hidden, view), true);
  }

  assert.equal(await evaluate(() => document.querySelector('#live-status-text').textContent), 'Sistema operativo');
  assert.equal(await evaluate(() => document.querySelector('#job-error').hidden), false);
  await click('[data-dismiss-job-error]');
  assert.equal(await evaluate(() => document.querySelector('#job-error').hidden), true);
  assert.deepEqual(await evaluate(() => ['review', 'queued', 'to-generate-total', 'published-total'].map((id) => document.getElementById(id).textContent)), ['1', '1', '1', '1']);

  await click('[data-video-filter="all"]');
  await setValue('#video-search', 'crossbow');
  assert.equal(await evaluate(() => document.querySelectorAll('#video-inventory tr[data-id]').length), 1);
  await setValue('#video-search', '');
  await click('tr[data-id="mc-02"] [data-action="inspect"]');
  assert.match(await evaluate(() => document.querySelector('#preview-title').textContent), /mc-02/);
  await clickRequest('#manual-publish [data-publish-platform="youtube"]', '/api/publish-platform');

  await click('tr[data-id="mc-02"] .row-menu summary');
  assert.equal(await evaluate(() => document.querySelector('tr[data-id="mc-02"] .row-menu').open), true);
  for (const action of ['video', 'audio', 'hints']) {
    await new Promise((resolve) => setTimeout(resolve, 100));
    if (!(await evaluate(() => document.querySelector('tr[data-id="mc-02"] .row-menu').open))) await click('tr[data-id="mc-02"] .row-menu summary');
    const before = requestCount('/api/action');
    await click(`tr[data-id="mc-02"] [data-action="${action}"]`);
    await waitNode(`action ${action}`, () => requestCount('/api/action') > before);
    if (action === 'hints') await waitPage('hints state', () => Boolean(document.querySelector('tr[data-id="mc-02"] [data-action="clear-hints"]')));
  }
  if (!(await evaluate(() => document.querySelector('tr[data-id="mc-02"] .row-menu').open))) await click('tr[data-id="mc-02"] .row-menu summary');
  await clickRequest('tr[data-id="mc-02"] [data-action="clear-hints"]', '/api/action');
  await waitPage('clear hints state', () => Boolean(document.querySelector('tr[data-id="mc-02"] [data-action="approve"]')));
  await clickRequest('tr[data-id="mc-02"] [data-action="approve"]', '/api/action');
  await waitPage('approved row', () => Boolean(document.querySelector('tr[data-id="mc-02"] [data-action="unqueue"]')));
  await clickRequest('tr[data-id="mc-02"] [data-action="unqueue"]', '/api/action');

  await clickRequest('tr[data-id="mc-01"] [data-action="generate"]', '/api/generate');
  await waitPage('cancel control', () => !document.querySelector('[data-cancel-job]').hidden);
  await clickRequest('[data-cancel-job]', '/api/job/cancel');
  await waitPage('generation controls restored', () => !document.querySelector('#random').disabled);
  await clickRequest('#random', '/api/generate');
  await waitPage('random cancel control', () => !document.querySelector('[data-cancel-job]').hidden);
  await clickRequest('[data-cancel-job]', '/api/job/cancel');
  await waitPage('random cancellation restored', () => !document.querySelector('#random').disabled);

  await click('[data-view="music"]');
  await setValue('#music-url', 'https://youtu.be/fixture');
  await setValue('#music-starts', '0:12, 0:34');
  await evaluate(() => { document.querySelector('#music-rights').checked = true; });
  await clickRequest('#music-import', '/api/music/import');
  await setValue('[data-original-starts]', '0:20');
  await clickRequest('[data-save-original]', '/api/music/original-starts');
  await clickRequest('[data-delete-track]', '/api/music/delete');

  await click('[data-view="analytics"]');
  assert.equal(await evaluate(() => Boolean(document.querySelector('#analytics-chart svg'))), true);
  await setValue('#analytics-platform', 'youtube', 'change');
  await setValue('#analytics-window', 'all', 'change');
  assert.equal(await evaluate(() => Boolean(document.querySelector('#analytics-chart svg'))), true);
  assert.equal(await evaluate(() => document.querySelectorAll('#analytics-cohorts-rows tr').length), 1);
  await setValue('#analytics-cohort-dimension', 'targetKind', 'change');
  assert.equal(await evaluate(() => document.querySelector('#analytics-cohorts-wrap').hidden), true);
  assert.equal(await evaluate(() => document.querySelectorAll('#analytics-quality-rows tr').length), 1);
  assert.match(await evaluate(() => document.querySelector('#analytics-alerts').textContent), /Fixture alert/);
  assert.match(await evaluate(() => document.querySelector('#analytics-recommendations').textContent), /Fixture recommendation/);
  await clickRequest('#sync-analytics', '/api/analytics/sync');
  assert.deepEqual(await evaluate(() => [...document.querySelectorAll('a[href^="/api/analytics/export"]')].map((link) => link.getAttribute('href'))), ['/api/analytics/export.json', '/api/analytics/export.md']);

  await click('[data-view="publishing"]');
  await evaluate(() => { document.querySelectorAll('.automation-details').forEach((details) => { details.open = true; }); document.querySelector('.credentials-details').open = true; });
  await setValue('#youtube-title', 'Updated {kind}');
  await clickRequest('#save-publishing', '/api/publishing/config');
  assert.equal(requests.filter((item) => item.path === '/api/publishing/config').at(-1).body.config.platforms.youtube.title, 'Updated {kind}');
  await clickRequest('#publish-now', '/api/publish-now');
  await setValue('#credentials-form input[name="YOUTUBE_CLIENT_ID"]', 'fixture-client');
  await clickRequest('#save-secrets', '/api/publishing/secrets');
  await clickRequest('#tiktok-disconnect', '/api/tiktok/disconnect');
  await waitPage('TikTok disconnected', () => !document.querySelector('#tiktok-connect').hidden);

  await click('[data-view="system"]');
  failNext = '/api/backup';
  await clickRequest('#make-backup', '/api/backup');
  await waitPage('visible API error', () => document.querySelector('#toast').textContent === 'Fallo controlado');
  await clickRequest('#make-backup', '/api/backup');
  await clickRequest('#make-snapshot', '/api/context-snapshot');
  const readsBefore = diagnosticsReads;
  await click('#refresh-system');
  await waitNode('diagnostics refresh', () => diagnosticsReads > readsBefore);

  await click('[data-view="home"]');
  await click('[data-video-filter="all"]');
  await click('tr[data-id="mc-02"] .row-menu summary');
  await clickRequest('tr[data-id="mc-02"] [data-action="reject"]', '/api/action');
  await waitPage('rejected row removed', () => !document.querySelector('tr[data-id="mc-02"]'));

  const requiredPaths = new Set([
    '/api/action', '/api/generate', '/api/job/cancel', '/api/publish-platform', '/api/music/import',
    '/api/music/original-starts', '/api/music/delete', '/api/analytics/sync', '/api/publishing/config',
    '/api/publish-now', '/api/publishing/secrets', '/api/tiktok/disconnect', '/api/backup', '/api/context-snapshot',
  ]);
  assert.deepEqual(new Set(requests.map((item) => item.path).filter((value) => requiredPaths.has(value))), requiredPaths);
  assert.equal(browserErrors.length, 0, browserErrors.join('\n'));
  assert.equal(JSON.stringify(requests).includes('token'), false);
  console.log('ok: dashboard browser navigation, filters, inspector, controls, errors, and every visible action');
} catch (error) {
  console.error(`dashboard UI failed: ${error.stack || error}`);
  console.error(`recent requests: ${requests.slice(-12).map((item) => item.path).join(', ')}`);
  process.exitCode = 1;
} finally {
  if (browser) await browser.close({silent: true});
  await new Promise((resolve) => server.close(resolve));
}
