/* Titelseite: lädt die aktuelle Ausgabe und rendert sie ins Zeitungs-Layout. */
(function () {
  var CACHE_KEY = "omazeitung_last_edition";

  function renderEdition(edition) {
    document.getElementById("edition-date").textContent = OmaZeitung.formatFolio(edition);
    OmaZeitung.renderArticleList(document.getElementById("lokal-list"), edition.articles.lokal);
    OmaZeitung.renderArticleList(document.getElementById("welt-list"), edition.articles.welt);
    OmaZeitung.renderArticleList(document.getElementById("sport-list"), edition.articles.sport);
    OmaZeitung.renderWeather(document.getElementById("weather-box"), edition.weather);
    OmaZeitung.renderHistory(document.getElementById("history-box"), edition.history);

    document.getElementById("content-status").hidden = true;
    document.getElementById("paper-grid").hidden = false;
  }

  function showOfflineBanner(visible) {
    document.getElementById("offline-banner").classList.toggle("visible", visible);
  }

  function loadEdition() {
    fetch("data/latest.json", { cache: "no-cache" })
      .then(function (res) {
        if (!res.ok) throw new Error("Keine Ausgabe verfügbar");
        return res.json();
      })
      .then(function (edition) {
        localStorage.setItem(CACHE_KEY, JSON.stringify(edition));
        showOfflineBanner(false);
        renderEdition(edition);
      })
      .catch(function () {
        var cached = localStorage.getItem(CACHE_KEY);
        if (cached) {
          showOfflineBanner(true);
          renderEdition(JSON.parse(cached));
        } else {
          document.getElementById("content-status").textContent =
            "Es konnte keine Ausgabe geladen werden. Bitte Internetverbindung prüfen.";
        }
      });
  }

  document.addEventListener("DOMContentLoaded", function () {
    loadEdition();
    var printBtn = document.getElementById("print-btn");
    if (printBtn) printBtn.addEventListener("click", function () { window.print(); });
  });
})();
