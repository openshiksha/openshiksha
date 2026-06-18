/*
 * MPN-3: Web Push handler, layered onto the generated service worker via
 * `workbox.importScripts` (vite.config.ts). We keep the generateSW precache
 * strategy (MSO-3) untouched and only add `push` + `notificationclick`
 * listeners on top — lowest-risk way to add push without switching to
 * injectManifest.
 *
 * Payload shape (from core.push.send_web_push): { title, body, url, tag }.
 */

self.addEventListener('push', (event) => {
  let data = {};
  try {
    data = event.data ? event.data.json() : {};
  } catch (e) {
    data = { body: event.data ? event.data.text() : '' };
  }
  const title = data.title || 'OpenShiksha';
  event.waitUntil(
    self.registration.showNotification(title, {
      body: data.body || '',
      icon: '/icons/icon-192.png',
      badge: '/icons/icon-192.png',
      data: { url: data.url || '/' },
      tag: data.tag,
    }),
  );
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const url = (event.notification.data && event.notification.data.url) || '/';
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
      const hit = clientList.find((c) => c.url.includes(url));
      if (hit) return hit.focus();
      return clients.openWindow(url);
    }),
  );
});
