/* Gemeinsame Render-Funktionen für eine Zeitungs-Ausgabe (genutzt von Titelseite + Archiv). */
var OmaZeitung = (function () {
  var WEEKDAYS = ["Sonntag", "Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag"];
  var MONTHS = [
    "Januar", "Februar", "März", "April", "Mai", "Juni",
    "Juli", "August", "September", "Oktober", "November", "Dezember"
  ];

  function formatDateLong(dateStr) {
    var d = new Date(dateStr + "T00:00:00");
    if (isNaN(d.getTime())) return dateStr;
    return WEEKDAYS[d.getDay()] + ", " + d.getDate() + ". " + MONTHS[d.getMonth()] + " " + d.getFullYear();
  }

  function formatFolio(edition) {
    var base = formatDateLong(edition.date);
    if (edition.issue_number) base += " · Ausgabe Nr. " + edition.issue_number;
    return base;
  }

  function el(tag, className, html) {
    var e = document.createElement(tag);
    if (className) e.className = className;
    if (html !== undefined) e.innerHTML = html;
    return e;
  }

  function renderArticleList(container, articles) {
    container.innerHTML = "";
    if (!articles || articles.length === 0) {
      container.appendChild(el("p", "empty-hint", "Für diese Rubrik liegen keine Meldungen vor."));
      return;
    }
    articles.forEach(function (a, idx) {
      var art = el("article", "news-item" + (idx === 0 ? " news-item--lead" : ""));
      art.appendChild(el("h3", null, a.title));
      if (a.source_name) art.appendChild(el("p", "news-meta", a.source_name));

      var paragraphs = (a.summary || "").split(/\n\s*\n/).map(function (p) { return p.trim(); }).filter(Boolean);
      if (paragraphs.length === 0) paragraphs = [a.summary || ""];
      paragraphs.forEach(function (text, pIdx) {
        art.appendChild(el("p", pIdx === 0 ? "news-body" : null, text));
      });

      if (a.source_url) {
        var link = el("a", "source-link", "Weiterlesen im Original ↗");
        link.href = a.source_url;
        link.target = "_blank";
        link.rel = "noopener noreferrer";
        art.appendChild(link);
      }
      container.appendChild(art);
    });
  }

  function renderWeather(root, weather) {
    var emojiEl = root.querySelector("[data-weather-emoji]");
    var tempEl = root.querySelector("[data-weather-temp]");
    var metaEl = root.querySelector("[data-weather-meta]");
    if (!weather || weather.temp_current === null || weather.temp_current === undefined) {
      emojiEl.textContent = "🌡️";
      tempEl.textContent = "-";
      metaEl.textContent = "Wetterdaten nicht verfügbar.";
      return;
    }
    emojiEl.textContent = weather.emoji || "🌡️";
    tempEl.textContent = Math.round(weather.temp_current) + "°C";
    var parts = [];
    parts.push(weather.description || "");
    if (weather.temp_min !== null && weather.temp_max !== null) {
      parts.push(Math.round(weather.temp_min) + "° bis " + Math.round(weather.temp_max) + "°C");
    }
    if (weather.precipitation_prob !== null && weather.precipitation_prob !== undefined) {
      parts.push("Regen " + weather.precipitation_prob + "%");
    }
    metaEl.textContent = (weather.location || "") + " · " + parts.filter(Boolean).join(" · ");
  }

  function renderHistory(root, history) {
    var container = root.querySelector("[data-history-content]");
    container.innerHTML = "";
    if (!history) {
      container.appendChild(el("p", "empty-hint", "Kein historischer Rückblick verfügbar."));
      return;
    }
    container.appendChild(
      el("p", "history-box__year", "Vor " + history.years_ago + " Jahren, im Jahr " + history.year)
    );
    container.appendChild(el("p", null, history.event_text));
  }

  return {
    formatDateLong: formatDateLong,
    formatFolio: formatFolio,
    el: el,
    renderArticleList: renderArticleList,
    renderWeather: renderWeather,
    renderHistory: renderHistory
  };
})();
