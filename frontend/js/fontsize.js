/* Schriftgrößen-Regler: A- / A / A+, speichert Wahl in LocalStorage */
(function () {
  var SCALES = { small: 0.85, medium: 1, large: 1.25 };
  var STORAGE_KEY = "omazeitung_fontsize";

  function applyScale(size) {
    var scale = SCALES[size] || 1;
    document.documentElement.style.setProperty("--font-scale", scale);
    document.querySelectorAll(".fontsize-btn").forEach(function (btn) {
      btn.classList.toggle("active", btn.dataset.size === size);
    });
  }

  function initFontSizeControls() {
    var saved = localStorage.getItem(STORAGE_KEY) || "medium";
    applyScale(saved);
    document.querySelectorAll(".fontsize-btn").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var size = btn.dataset.size;
        localStorage.setItem(STORAGE_KEY, size);
        applyScale(size);
      });
    });
  }

  document.addEventListener("DOMContentLoaded", initFontSizeControls);
})();
