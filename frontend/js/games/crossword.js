/* Kreuzworträtsel: lädt das Tagesrätsel, Touch-Eingabe über Gitter-Felder + Klick-Klueliste. */
(function () {
  var gridEl = document.getElementById("crossword-grid");
  var cluesEl = document.getElementById("crossword-clues");
  var acrossListEl = document.getElementById("clues-across");
  var downListEl = document.getElementById("clues-down");
  var statusEl = document.getElementById("crossword-status");
  var checkBtn = document.getElementById("cw-check-btn");

  var solutionCells = null; // [[letter|null]]
  var words = [];
  var selected = null;
  var currentDirection = "across";
  var storageKey = null;

  function inputId(r, c) { return "cw-" + r + "-" + c; }

  function coversCell(word, r, c) {
    if (word.direction === "across") {
      return r === word.row && c >= word.col && c < word.col + word.length;
    }
    return c === word.col && r >= word.row && r < word.row + word.length;
  }

  function wordsAt(r, c) {
    return words.filter(function (w) { return coversCell(w, r, c); });
  }

  function numberForCell(r, c) {
    var w = words.find(function (w) { return w.row === r && w.col === c; });
    return w ? w.number : null;
  }

  function saveProgress() {
    if (!storageKey) return;
    var values = {};
    document.querySelectorAll(".crossword-cell").forEach(function (inp) {
      if (inp.value) values[inp.id] = inp.value;
    });
    localStorage.setItem(storageKey, JSON.stringify(values));
  }

  function loadProgress() {
    if (!storageKey) return {};
    var raw = localStorage.getItem(storageKey);
    return raw ? JSON.parse(raw) : {};
  }

  function renderGrid(width, height) {
    gridEl.innerHTML = "";
    gridEl.style.gridTemplateColumns = "repeat(" + width + ", 40px)";
    gridEl.style.gridTemplateRows = "repeat(" + height + ", 40px)";
    var saved = loadProgress();

    for (var r = 0; r < height; r++) {
      for (var c = 0; c < width; c++) {
        var isBlocked = solutionCells[r][c] === null;
        var wrap = document.createElement("div");
        wrap.className = "crossword-cell-wrap" + (isBlocked ? " blocked" : "");
        if (!isBlocked) {
          var num = numberForCell(r, c);
          if (num) {
            var numEl = document.createElement("span");
            numEl.className = "crossword-number";
            numEl.textContent = num;
            wrap.appendChild(numEl);
          }
          var input = document.createElement("input");
          input.type = "text";
          input.maxLength = 1;
          input.autocomplete = "off";
          input.className = "crossword-cell";
          input.id = inputId(r, c);
          input.dataset.r = r;
          input.dataset.c = c;
          if (saved[input.id]) input.value = saved[input.id];

          input.addEventListener("focus", function () {
            selectCell(parseInt(this.dataset.r, 10), parseInt(this.dataset.c, 10), false);
          });
          input.addEventListener("input", function () {
            this.value = this.value.toUpperCase().replace(/[^A-ZÄÖÜ]/g, "");
            saveProgress();
            if (this.value) moveInDirection(parseInt(this.dataset.r, 10), parseInt(this.dataset.c, 10), 1);
          });
          input.addEventListener("keydown", function (e) {
            if (e.key === "Backspace" && !this.value) {
              moveInDirection(parseInt(this.dataset.r, 10), parseInt(this.dataset.c, 10), -1);
            }
          });
          wrap.appendChild(input);
        }
        gridEl.appendChild(wrap);
      }
    }
  }

  function activeWord() {
    if (!selected) return null;
    var here = wordsAt(selected.r, selected.c);
    return here.find(function (w) { return w.direction === currentDirection; }) || here[0] || null;
  }

  function moveInDirection(r, c, step) {
    var word = activeWord();
    if (!word) return;
    var nr = r, nc = c;
    if (word.direction === "across") nc += step; else nr += step;
    var input = document.getElementById(inputId(nr, nc));
    if (input) input.focus();
  }

  function updateHighlight() {
    document.querySelectorAll(".crossword-cell").forEach(function (el) { el.classList.remove("active-word", "active-cell"); });
    document.querySelectorAll(".crossword-clues li").forEach(function (li) { li.classList.remove("active"); });

    var word = activeWord();
    if (!word) return;
    for (var i = 0; i < word.length; i++) {
      var r = word.row + (word.direction === "down" ? i : 0);
      var c = word.col + (word.direction === "across" ? i : 0);
      var el = document.getElementById(inputId(r, c));
      if (el) el.classList.add("active-word");
    }
    if (selected) {
      var selEl = document.getElementById(inputId(selected.r, selected.c));
      if (selEl) selEl.classList.add("active-cell");
    }
    var li = document.getElementById("clue-" + word.direction + "-" + word.number);
    if (li) {
      li.classList.add("active");
      li.scrollIntoView({ block: "nearest" });
    }
  }

  function selectCell(r, c, forceToggle) {
    var here = wordsAt(r, c);
    if (here.length === 0) return;
    if (forceToggle === undefined) forceToggle = true;

    if (forceToggle && selected && selected.r === r && selected.c === c) {
      var other = here.find(function (w) { return w.direction !== currentDirection; });
      if (other) currentDirection = other.direction;
    } else {
      var same = here.find(function (w) { return w.direction === currentDirection; });
      if (!same) currentDirection = here[0].direction;
    }
    selected = { r: r, c: c };
    updateHighlight();
  }

  function selectWord(word) {
    currentDirection = word.direction;
    selected = { r: word.row, c: word.col };
    updateHighlight();
    var el = document.getElementById(inputId(word.row, word.col));
    if (el) el.focus();
  }

  function renderClues() {
    acrossListEl.innerHTML = "";
    downListEl.innerHTML = "";
    var across = words.filter(function (w) { return w.direction === "across"; }).sort(function (a, b) { return a.number - b.number; });
    var down = words.filter(function (w) { return w.direction === "down"; }).sort(function (a, b) { return a.number - b.number; });

    function buildLi(w) {
      var li = document.createElement("li");
      li.id = "clue-" + w.direction + "-" + w.number;
      li.textContent = w.number + ". " + w.clue + " (" + w.length + ")";
      li.addEventListener("click", function () { selectWord(w); });
      return li;
    }
    across.forEach(function (w) { acrossListEl.appendChild(buildLi(w)); });
    down.forEach(function (w) { downListEl.appendChild(buildLi(w)); });
  }

  function checkSolution() {
    var correct = 0, total = 0, complete = true;
    document.querySelectorAll(".crossword-cell").forEach(function (inp) {
      var r = parseInt(inp.dataset.r, 10), c = parseInt(inp.dataset.c, 10);
      total++;
      if (!inp.value) { complete = false; inp.classList.remove("error"); return; }
      if (inp.value === solutionCells[r][c]) {
        correct++;
        inp.classList.remove("error");
      } else {
        inp.classList.add("error");
      }
    });
    statusEl.hidden = false;
    if (!complete) {
      statusEl.textContent = "Noch nicht alle Felder ausgefüllt (" + correct + "/" + total + " richtig).";
    } else if (correct === total) {
      statusEl.textContent = "Klasse - alles richtig gelöst! 🎉";
    } else {
      statusEl.textContent = "Es sind noch " + (total - correct) + " Felder falsch (rot markiert).";
    }
  }

  function init(edition) {
    var data = edition.puzzles && edition.puzzles.crossword;
    if (!data || !data.words || data.words.length === 0) {
      statusEl.textContent = "Für heute ist noch kein Kreuzworträtsel verfügbar.";
      return;
    }
    solutionCells = data.cells;
    words = data.words;
    storageKey = "omazeitung_crossword_" + edition.date;

    statusEl.hidden = true;
    gridEl.hidden = false;
    cluesEl.hidden = false;
    checkBtn.hidden = false;

    renderGrid(data.width, data.height);
    renderClues();
  }

  document.addEventListener("DOMContentLoaded", function () {
    checkBtn.addEventListener("click", checkSolution);
    fetch("data/latest.json", { cache: "no-cache" })
      .then(function (res) {
        if (!res.ok) throw new Error("keine Ausgabe");
        return res.json();
      })
      .then(init)
      .catch(function () {
        statusEl.textContent = "Kreuzworträtsel konnte nicht geladen werden. Bitte Internetverbindung prüfen.";
      });
  });
})();
