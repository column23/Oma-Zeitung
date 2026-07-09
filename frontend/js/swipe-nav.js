/* Einfache Swipe-Geste zur Navigation zwischen den Hauptseiten (Titelseite/Sport/Spiele/Archiv) */
(function () {
  var PAGE_ORDER = ["index.html", "spiele.html", "archiv.html"];
  var THRESHOLD = 70;

  function currentPageIndex() {
    var file = location.pathname.split("/").pop() || "index.html";
    var idx = PAGE_ORDER.indexOf(file);
    return idx === -1 ? 0 : idx;
  }

  function initSwipeNav() {
    var startX = null;
    var startY = null;

    document.addEventListener(
      "touchstart",
      function (e) {
        if (e.touches.length !== 1) return;
        startX = e.touches[0].clientX;
        startY = e.touches[0].clientY;
      },
      { passive: true }
    );

    document.addEventListener(
      "touchend",
      function (e) {
        if (startX === null) return;
        var endX = e.changedTouches[0].clientX;
        var endY = e.changedTouches[0].clientY;
        var dx = endX - startX;
        var dy = endY - startY;
        startX = null;
        startY = null;

        if (Math.abs(dx) < THRESHOLD || Math.abs(dx) < Math.abs(dy) * 1.5) return;

        var idx = currentPageIndex();
        if (dx < 0 && idx < PAGE_ORDER.length - 1) {
          location.href = PAGE_ORDER[idx + 1];
        } else if (dx > 0 && idx > 0) {
          location.href = PAGE_ORDER[idx - 1];
        }
      },
      { passive: true }
    );
  }

  document.addEventListener("DOMContentLoaded", initSwipeNav);
})();
