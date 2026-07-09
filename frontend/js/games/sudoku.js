/* Sudoku-Spiel: lädt das Tagesrätsel und ermöglicht Touch-Eingabe über ein Zahlenfeld. */
(function () {
  var gridEl = document.getElementById("sudoku-grid");
  var numpadEl = document.getElementById("sudoku-numpad");
  var statusEl = document.getElementById("sudoku-status");
  var checkBtn = document.getElementById("check-btn");
  var resetBtn = document.getElementById("reset-btn");

  var puzzle = null;
  var solution = null;
  var given = null; // boolean grid: true = vorgegebene Zahl (nicht editierbar)
  var current = null; // aktueller Nutzer-Stand
  var selected = null; // {r, c}
  var storageKey = null;

  function saveProgress() {
    if (!storageKey) return;
    localStorage.setItem(storageKey, JSON.stringify(current));
  }

  function cellId(r, c) { return "cell-" + r + "-" + c; }

  function renderGrid() {
    gridEl.innerHTML = "";
    for (var r = 0; r < 9; r++) {
      for (var c = 0; c < 9; c++) {
        var btn = document.createElement("button");
        btn.type = "button";
        btn.id = cellId(r, c);
        btn.className = "sudoku-cell";
        if ((r + 1) % 3 === 0 && r !== 8) btn.classList.add("sudoku-row-thick");
        var value = current[r][c];
        if (given[r][c]) {
          btn.classList.add("given");
          btn.textContent = value;
          btn.disabled = true;
        } else {
          btn.textContent = value === 0 ? "" : value;
          btn.addEventListener("click", (function (row, col) {
            return function () { selectCell(row, col); };
          })(r, c));
        }
        gridEl.appendChild(btn);
      }
    }
  }

  function selectCell(r, c) {
    if (selected) {
      var prevEl = document.getElementById(cellId(selected.r, selected.c));
      if (prevEl) prevEl.classList.remove("active-cell");
    }
    selected = { r: r, c: c };
    document.getElementById(cellId(r, c)).classList.add("active-cell");
  }

  function renderNumpad() {
    numpadEl.innerHTML = "";
    for (var n = 1; n <= 9; n++) {
      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "numpad-btn";
      btn.textContent = n;
      btn.addEventListener("click", function () {
        setSelectedValue(parseInt(this.textContent, 10));
      });
      numpadEl.appendChild(btn);
    }
    var clearBtn = document.createElement("button");
    clearBtn.type = "button";
    clearBtn.className = "numpad-btn numpad-clear";
    clearBtn.textContent = "Löschen";
    clearBtn.addEventListener("click", function () { setSelectedValue(0); });
    numpadEl.appendChild(clearBtn);
  }

  function setSelectedValue(val) {
    if (!selected) return;
    var r = selected.r, c = selected.c;
    if (given[r][c]) return;
    current[r][c] = val;
    var el = document.getElementById(cellId(r, c));
    el.textContent = val === 0 ? "" : val;
    el.classList.remove("error");
    saveProgress();
  }

  function checkSolution() {
    var complete = true;
    var allCorrect = true;
    for (var r = 0; r < 9; r++) {
      for (var c = 0; c < 9; c++) {
        var el = document.getElementById(cellId(r, c));
        if (given[r][c]) continue;
        if (current[r][c] === 0) {
          complete = false;
          el.classList.remove("error");
          continue;
        }
        if (current[r][c] !== solution[r][c]) {
          allCorrect = false;
          el.classList.add("error");
        } else {
          el.classList.remove("error");
        }
      }
    }
    if (!complete) {
      statusEl.hidden = false;
      statusEl.className = "loading";
      statusEl.textContent = "Noch nicht alle Felder ausgefüllt.";
    } else if (allCorrect) {
      statusEl.hidden = false;
      statusEl.className = "loading";
      statusEl.textContent = "Super gemacht - das Sudoku ist richtig gelöst! 🎉";
    } else {
      statusEl.hidden = false;
      statusEl.className = "loading";
      statusEl.textContent = "Es sind noch Fehler enthalten (rot markiert).";
    }
  }

  function resetPuzzle() {
    current = puzzle.map(function (row) { return row.slice(); });
    saveProgress();
    renderGrid();
    statusEl.hidden = true;
  }

  function init(edition) {
    var data = edition.puzzles && edition.puzzles.sudoku;
    if (!data) {
      statusEl.textContent = "Für heute ist noch kein Sudoku verfügbar.";
      return;
    }
    puzzle = data.puzzle;
    solution = data.solution;
    given = puzzle.map(function (row) { return row.map(function (v) { return v !== 0; }); });
    storageKey = "omazeitung_sudoku_" + edition.date;

    var savedRaw = localStorage.getItem(storageKey);
    current = savedRaw ? JSON.parse(savedRaw) : puzzle.map(function (row) { return row.slice(); });

    statusEl.hidden = true;
    gridEl.hidden = false;
    numpadEl.hidden = false;
    checkBtn.hidden = false;
    resetBtn.hidden = false;

    renderGrid();
    renderNumpad();
  }

  document.addEventListener("DOMContentLoaded", function () {
    checkBtn.addEventListener("click", checkSolution);
    resetBtn.addEventListener("click", resetPuzzle);

    fetch("data/latest.json", { cache: "no-cache" })
      .then(function (res) {
        if (!res.ok) throw new Error("keine Ausgabe");
        return res.json();
      })
      .then(init)
      .catch(function () {
        statusEl.textContent = "Sudoku konnte nicht geladen werden. Bitte Internetverbindung prüfen.";
      });
  });
})();
