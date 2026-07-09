/* Registriert den Service Worker für Offline-Caching / Installierbarkeit als PWA. */
if ("serviceWorker" in navigator) {
  window.addEventListener("load", function () {
    navigator.serviceWorker.register("service-worker.js").catch(function (err) {
      console.warn("Service Worker Registrierung fehlgeschlagen:", err);
    });
  });
}
