/* Service Worker: cached App-Shell + zuletzt geladene Ausgabe für Offline-Nutzung.
   Alle Pfade sind RELATIV zum Service-Worker-Verzeichnis, damit die App sowohl lokal
   (Root) als auch bei GitHub Pages unter einem Unterpfad (/<repo>/) funktioniert. */
var CACHE_NAME = "omazeitung-cache-v2";

var APP_SHELL = [
  "./",
  "index.html",
  "archiv.html",
  "spiele.html",
  "sudoku.html",
  "kreuzwortraetsel.html",
  "solitaer.html",
  "manifest.json",
  "css/style.css",
  "css/games.css",
  "css/archiv.css",
  "js/app.js",
  "js/fontsize.js",
  "js/swipe-nav.js",
  "js/sw-register.js",
  "js/edition-render.js",
  "js/archiv.js",
  "js/games/sudoku.js",
  "js/games/crossword.js",
  "js/games/solitaire.js",
  "icons/icon-192.png",
  "icons/icon-512.png",
  "icons/icon-maskable-512.png"
];

self.addEventListener("install", function (event) {
  event.waitUntil(
    caches.open(CACHE_NAME).then(function (cache) {
      return Promise.all(
        APP_SHELL.map(function (url) {
          return cache.add(url).catch(function () {
            /* einzelne fehlende Datei ignorieren, App-Shell-Installation nicht blockieren */
          });
        })
      );
    })
  );
  self.skipWaiting();
});

self.addEventListener("activate", function (event) {
  event.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(
        keys.filter(function (key) { return key !== CACHE_NAME; }).map(function (key) { return caches.delete(key); })
      );
    })
  );
  self.clients.claim();
});

function isEditionData(url) {
  // Tages-Inhalte unter data/ (latest.json, index.json, <datum>.json)
  return url.pathname.indexOf("/data/") !== -1 && url.pathname.slice(-5) === ".json";
}

self.addEventListener("fetch", function (event) {
  var request = event.request;
  if (request.method !== "GET") return;

  var url = new URL(request.url);
  if (url.origin !== self.location.origin) return; // externe Requests nicht abfangen

  if (isEditionData(url)) {
    // Network-first: aktuelle Ausgabe möglichst frisch, sonst letzte gecachte Version
    event.respondWith(
      fetch(request)
        .then(function (response) {
          var copy = response.clone();
          caches.open(CACHE_NAME).then(function (cache) { cache.put(request, copy); });
          return response;
        })
        .catch(function () {
          return caches.match(request);
        })
    );
    return;
  }

  // App-Shell / statische Dateien: cache-first
  event.respondWith(
    caches.match(request).then(function (cached) {
      if (cached) return cached;
      return fetch(request)
        .then(function (response) {
          var copy = response.clone();
          caches.open(CACHE_NAME).then(function (cache) { cache.put(request, copy); });
          return response;
        })
        .catch(function () {
          if (request.mode === "navigate") return caches.match("index.html");
        });
    })
  );
});
