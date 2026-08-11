// 个人 AI 工作台 — Service Worker（PWA 离线壳 + 运行时缓存）
// 作用：首次打开后预缓存应用壳，之后离线也能开；API 用 stale-while-revalidate。
const CACHE = 'workbench-shell-v1';
const SHELL = [
  '/',
  '/index.html',
  '/manifest.json',
  '/static/echarts.min.js',
  '/static/icon.svg',
];

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET') return;            // 只缓存 GET
  const url = new URL(req.url);

  // 壳资源：缓存优先（离线可开）
  if (SHELL.includes(url.pathname)) {
    e.respondWith(caches.match(req).then((hit) => hit || fetch(req)));
    return;
  }

  // API：先给缓存，后台静默更新（stale-while-revalidate）
  if (url.pathname.startsWith('/api/')) {
    e.respondWith(
      caches.open(CACHE).then(async (c) => {
        const hit = await c.match(req);
        const net = fetch(req)
          .then((res) => { if (res.ok) c.put(req, res.clone()); return res; })
          .catch(() => hit);
        return hit || net;
      })
    );
    return;
  }

  // 其余：网络优先，失败回退缓存
  e.respondWith(fetch(req).catch(() => caches.match(req)));
});
