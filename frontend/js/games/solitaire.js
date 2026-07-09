/* Solitär (Klondike) - eigenständiges Browserspiel mit Touch-Drag&Drop (Pointer Events). */
(function () {
  var SUITS = ["H", "D", "C", "S"];
  var SUIT_SYMBOL = { H: "♥", D: "♦", C: "♣", S: "♠" };
  var RED_SUITS = { H: true, D: true };
  var OFFSET_STEP = 28;
  var DRAG_THRESHOLD = 6;

  var board = document.getElementById("solitaire-board");
  var winBanner = document.getElementById("win-banner");

  var state = null; // { stock:[], waste:[], foundations:{H:[],D:[],C:[],S:[]}, tableau:[[],[],...] }

  function rankLabel(rank) {
    if (rank === 1) return "A";
    if (rank === 11) return "B";
    if (rank === 12) return "D";
    if (rank === 13) return "K";
    return String(rank);
  }

  function isRed(suit) { return !!RED_SUITS[suit]; }

  function makeDeck() {
    var deck = [];
    SUITS.forEach(function (suit) {
      for (var rank = 1; rank <= 13; rank++) {
        deck.push({ suit: suit, rank: rank, faceUp: false, id: suit + rank });
      }
    });
    for (var i = deck.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random() * (i + 1));
      var tmp = deck[i]; deck[i] = deck[j]; deck[j] = tmp;
    }
    return deck;
  }

  function newGame() {
    var deck = makeDeck();
    var tableau = [[], [], [], [], [], [], []];
    for (var col = 0; col < 7; col++) {
      for (var k = 0; k <= col; k++) {
        var card = deck.pop();
        card.faceUp = k === col;
        tableau[col].push(card);
      }
    }
    var stock = deck.map(function (c) { c.faceUp = false; return c; });

    state = {
      stock: stock,
      waste: [],
      foundations: { H: [], D: [], C: [], S: [] },
      tableau: tableau
    };
    winBanner.hidden = true;
    render();
  }

  // ---------- Regeln ----------

  function canDropOnFoundation(card, suit) {
    var pile = state.foundations[suit];
    if (card.suit !== suit) return false;
    if (pile.length === 0) return card.rank === 1;
    return pile[pile.length - 1].rank === card.rank - 1;
  }

  function canDropOnTableau(card, colIndex) {
    var pile = state.tableau[colIndex];
    if (pile.length === 0) return card.rank === 13;
    var top = pile[pile.length - 1];
    if (!top.faceUp) return false;
    return top.rank === card.rank + 1 && isRed(top.suit) !== isRed(card.suit);
  }

  function checkWin() {
    var total = 0;
    SUITS.forEach(function (s) { total += state.foundations[s].length; });
    if (total === 52) {
      winBanner.hidden = false;
    }
  }

  // ---------- Rendering ----------

  function buildCardEl(card) {
    var div = document.createElement("div");
    div.className = "playing-card " + (isRed(card.suit) ? "red" : "black") + (card.faceUp ? "" : " face-down");
    div.dataset.suit = card.suit;
    div.dataset.rank = card.rank;
    div.dataset.id = card.id;
    if (card.faceUp) {
      var label = rankLabel(card.rank) + SUIT_SYMBOL[card.suit];
      div.innerHTML =
        '<span class="card-corner top">' + label + "</span>" +
        '<span style="text-align:center;font-size:1.6rem;">' + SUIT_SYMBOL[card.suit] + "</span>" +
        '<span class="card-corner bottom">' + label + "</span>";
    }
    return div;
  }

  function render() {
    // Stock
    var stockEl = document.getElementById("pile-stock");
    stockEl.innerHTML = "";
    if (state.stock.length > 0) {
      var backCard = buildCardEl({ suit: "S", rank: 1, faceUp: false, id: "stockback" });
      stockEl.appendChild(backCard);
    }

    // Waste
    var wasteEl = document.getElementById("pile-waste");
    wasteEl.innerHTML = "";
    if (state.waste.length > 0) {
      var topWaste = state.waste[state.waste.length - 1];
      wasteEl.appendChild(buildCardEl(topWaste));
    }

    // Foundations
    SUITS.forEach(function (suit) {
      var el = document.getElementById("pile-foundation-" + suit);
      el.innerHTML = "";
      var pile = state.foundations[suit];
      if (pile.length > 0) {
        el.appendChild(buildCardEl(pile[pile.length - 1]));
      } else {
        var hint = document.createElement("span");
        hint.style.cssText = "position:absolute;inset:0;display:flex;align-items:center;justify-content:center;color:#bbb;font-size:1.4rem;";
        hint.textContent = SUIT_SYMBOL[suit];
        el.appendChild(hint);
      }
    });

    // Tableau
    for (var col = 0; col < 7; col++) {
      var slot = document.getElementById("tableau-" + col);
      slot.innerHTML = "";
      var pile = state.tableau[col];
      pile.forEach(function (card, idx) {
        var el = buildCardEl(card);
        el.style.top = (idx * OFFSET_STEP) + "px";
        el.style.zIndex = idx;
        slot.appendChild(el);
      });
      slot.style.minHeight = (118 + Math.max(0, pile.length - 1) * OFFSET_STEP) + "px";
    }

    checkWin();
    attachHandlers();
  }

  // ---------- Interaktion (Stock/Waste Klick + Drag&Drop) ----------

  function drawFromStock() {
    if (state.stock.length === 0) {
      // Waste zurück auf Stock (umgedreht)
      state.stock = state.waste.reverse().map(function (c) { c.faceUp = false; return c; });
      state.waste = [];
    } else {
      var card = state.stock.pop();
      card.faceUp = true;
      state.waste.push(card);
    }
    render();
  }

  function tryAutoMoveToFoundation(card, fromLocation) {
    for (var i = 0; i < SUITS.length; i++) {
      var suit = SUITS[i];
      if (canDropOnFoundation(card, suit)) {
        removeCardFromSource(fromLocation);
        state.foundations[suit].push(card);
        flipNewTopIfNeeded(fromLocation);
        render();
        return true;
      }
    }
    return false;
  }

  function flipNewTopIfNeeded(location) {
    if (location.type === "tableau") {
      var pile = state.tableau[location.col];
      if (pile.length > 0) pile[pile.length - 1].faceUp = true;
    }
  }

  function removeCardFromSource(location) {
    if (location.type === "waste") {
      state.waste.pop();
    } else if (location.type === "tableau") {
      state.tableau[location.col] = state.tableau[location.col].slice(0, location.index);
    } else if (location.type === "foundation") {
      state.foundations[location.suit].pop();
    }
  }

  function getMovingGroup(location) {
    if (location.type === "waste") {
      return state.waste.length ? [state.waste[state.waste.length - 1]] : [];
    }
    if (location.type === "tableau") {
      var pile = state.tableau[location.col];
      return pile.slice(location.index);
    }
    return [];
  }

  function locateCardElement(cardId) {
    return board.querySelector('[data-id="' + cardId + '"]');
  }

  var drag = null; // { location, cards, ghostEls, startX, startY, moved }

  function pointerDownOnCard(e, location) {
    if (location.type === "tableau") {
      var pile = state.tableau[location.col];
      if (!pile[location.index].faceUp) return;
    }
    if (location.type === "foundation") return; // Karten aus Foundation nicht wegziehbar

    var cards = getMovingGroup(location);
    if (cards.length === 0) return;

    var originEl = e.currentTarget;
    var rect = originEl.getBoundingClientRect();

    drag = {
      location: location,
      cards: cards,
      startX: e.clientX,
      startY: e.clientY,
      offsetX: e.clientX - rect.left,
      offsetY: e.clientY - rect.top,
      moved: false,
      ghostEls: []
    };

    cards.forEach(function (card, i) {
      var ghost = buildCardEl(card);
      ghost.classList.add("dragging");
      ghost.style.position = "fixed";
      ghost.style.left = (rect.left) + "px";
      ghost.style.top = (rect.top + i * OFFSET_STEP) + "px";
      ghost.style.pointerEvents = "none";
      document.body.appendChild(ghost);
      drag.ghostEls.push(ghost);
    });

    document.addEventListener("pointermove", onPointerMove);
    document.addEventListener("pointerup", onPointerUp);
  }

  function onPointerMove(e) {
    if (!drag) return;
    var dx = e.clientX - drag.startX;
    var dy = e.clientY - drag.startY;
    if (Math.abs(dx) > DRAG_THRESHOLD || Math.abs(dy) > DRAG_THRESHOLD) drag.moved = true;
    drag.ghostEls.forEach(function (ghost, i) {
      ghost.style.left = (e.clientX - drag.offsetX) + "px";
      ghost.style.top = (e.clientY - drag.offsetY + i * OFFSET_STEP) + "px";
    });
  }

  function findDropTarget(x, y) {
    drag.ghostEls.forEach(function (g) { g.style.display = "none"; });
    var el = document.elementFromPoint(x, y);
    drag.ghostEls.forEach(function (g) { g.style.display = ""; });
    if (!el) return null;
    var pileEl = el.closest("[id^='pile-foundation-']");
    if (pileEl) return { type: "foundation", suit: pileEl.dataset.suit };
    var tabEl = el.closest(".tableau-slot");
    if (tabEl) return { type: "tableau", col: parseInt(tabEl.dataset.col, 10) };
    return null;
  }

  function cleanupDrag() {
    drag.ghostEls.forEach(function (g) { g.remove(); });
    document.removeEventListener("pointermove", onPointerMove);
    document.removeEventListener("pointerup", onPointerUp);
    drag = null;
  }

  function onPointerUp(e) {
    if (!drag) return;
    var wasMoved = drag.moved;
    var location = drag.location;
    var cards = drag.cards;

    if (!wasMoved) {
      cleanupDrag();
      // Kurzer Tipp: automatisch auf Foundation legen, wenn möglich (nur oberste Einzelkarte)
      if (cards.length === 1) {
        tryAutoMoveToFoundation(cards[0], location);
      }
      return;
    }

    var target = findDropTarget(e.clientX, e.clientY);
    cleanupDrag();

    if (!target) { render(); return; }

    if (target.type === "foundation" && cards.length === 1 && canDropOnFoundation(cards[0], target.suit)) {
      removeCardFromSource(location);
      state.foundations[target.suit].push(cards[0]);
      flipNewTopIfNeeded(location);
      render();
      return;
    }

    if (target.type === "tableau" && canDropOnTableau(cards[0], target.col)) {
      // Nicht auf die eigene Quellspalte ablegen
      if (location.type === "tableau" && location.col === target.col) { render(); return; }
      removeCardFromSource(location);
      cards.forEach(function (c) { c.faceUp = true; });
      state.tableau[target.col] = state.tableau[target.col].concat(cards);
      flipNewTopIfNeeded(location);
      render();
      return;
    }

    render(); // ungültiger Zug -> Karte springt zurück
  }

  function attachHandlers() {
    document.getElementById("pile-stock").onclick = drawFromStock;

    var wasteCard = document.querySelector('#pile-waste .playing-card');
    if (wasteCard) {
      wasteCard.addEventListener("pointerdown", function (e) {
        pointerDownOnCard(e, { type: "waste" });
      });
    }

    for (var col = 0; col < 7; col++) {
      (function (col) {
        var pile = state.tableau[col];
        var cardEls = document.querySelectorAll("#tableau-" + col + " .playing-card");
        cardEls.forEach(function (el, idx) {
          el.addEventListener("pointerdown", function (e) {
            pointerDownOnCard(e, { type: "tableau", col: col, index: idx });
          });
        });
      })(col);
    }
  }

  document.getElementById("new-game-btn").addEventListener("click", newGame);
  document.addEventListener("DOMContentLoaded", newGame);
})();
