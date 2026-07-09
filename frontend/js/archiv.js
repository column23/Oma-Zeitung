/* Archiv-Seite: Liste vergangener Ausgaben, Datumssuche, Detailansicht. */
(function () {
  var listView = document.getElementById("list-view");
  var detailView = document.getElementById("detail-view");
  var editionsList = document.getElementById("editions-list");
  var searchInput = document.getElementById("date-search");

  var allEditions = null; // einmal geladene Gesamtliste, danach clientseitig gefiltert

  function loadList(search) {
    if (allEditions !== null) {
      renderFiltered(search);
      return;
    }
    editionsList.className = "loading";
    editionsList.textContent = "Ausgaben werden geladen ...";
    fetch("data/index.json", { cache: "no-cache" })
      .then(function (res) {
        if (!res.ok) throw new Error("kein Archiv");
        return res.json();
      })
      .then(function (editions) {
        allEditions = Array.isArray(editions) ? editions : [];
        renderFiltered(search);
      })
      .catch(function () {
        editionsList.className = "empty-hint";
        editionsList.textContent = "Archiv konnte nicht geladen werden.";
      });
  }

  function renderFiltered(search) {
    var list = allEditions;
    if (search) {
      var needle = search.toLowerCase();
      list = allEditions.filter(function (ed) {
        return (ed.date || "").toLowerCase().indexOf(needle) !== -1;
      });
    }
    renderList(list);
  }

  function renderList(editions) {
    editionsList.className = "";
    editionsList.innerHTML = "";
    if (!editions || editions.length === 0) {
      editionsList.appendChild(OmaZeitung.el("p", "empty-hint", "Keine Ausgaben gefunden."));
      return;
    }
    editions.forEach(function (ed) {
      var btn = OmaZeitung.el(
        "button",
        "edition-entry",
        "<strong>" + OmaZeitung.formatDateLong(ed.date) + "</strong><span class=\"count\">" +
          ed.article_count + " Artikel</span>"
      );
      btn.addEventListener("click", function () { openDetail(ed.date); });
      editionsList.appendChild(btn);
    });
  }

  function openDetail(dateStr) {
    fetch("data/" + dateStr + ".json", { cache: "no-cache" })
      .then(function (res) {
        if (!res.ok) throw new Error("nicht gefunden");
        return res.json();
      })
      .then(function (edition) {
        document.getElementById("detail-date").textContent = OmaZeitung.formatFolio(edition);
        OmaZeitung.renderArticleList(document.getElementById("detail-lokal-list"), edition.articles.lokal);
        OmaZeitung.renderArticleList(document.getElementById("detail-welt-list"), edition.articles.welt);
        OmaZeitung.renderArticleList(document.getElementById("detail-sport-list"), edition.articles.sport);
        OmaZeitung.renderWeather(document.getElementById("detail-weather-box"), edition.weather);
        OmaZeitung.renderHistory(document.getElementById("detail-history-box"), edition.history);

        listView.hidden = true;
        detailView.hidden = false;
        window.scrollTo(0, 0);
      })
      .catch(function () {
        alert("Diese Ausgabe konnte nicht geladen werden.");
      });
  }

  document.getElementById("back-to-list").addEventListener("click", function () {
    detailView.hidden = true;
    listView.hidden = false;
  });

  document.getElementById("detail-print-btn").addEventListener("click", function () { window.print(); });

  document.getElementById("clear-search").addEventListener("click", function () {
    searchInput.value = "";
    loadList("");
  });

  var debounceTimer = null;
  searchInput.addEventListener("input", function () {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(function () { loadList(searchInput.value.trim()); }, 300);
  });

  loadList("");
})();
