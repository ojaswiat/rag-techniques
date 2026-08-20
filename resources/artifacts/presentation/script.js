/* Deck navigation. Keyboard-first, because the deck is driven live while
   screen-sharing: arrows or space to move, O for the overview grid, F for
   fullscreen. The slide index lives in location.hash so a reload, or a link
   handed to someone else, lands on the same slide. */

(function () {
  "use strict";

  var slides = [].slice.call(document.querySelectorAll(".slide"));
  var progress = document.getElementById("progress");
  var counter = document.getElementById("counter");
  var overview = document.getElementById("overview");
  var prevBtn = document.getElementById("prev");
  var nextBtn = document.getElementById("next");
  var current = 0;

  function clamp(i) {
    return Math.max(0, Math.min(slides.length - 1, i));
  }

  function show(i, push) {
    current = clamp(i);
    slides.forEach(function (s, n) {
      s.classList.toggle("active", n === current);
    });

    var pct = slides.length < 2 ? 100 : (current / (slides.length - 1)) * 100;
    progress.style.width = pct + "%";
    counter.innerHTML = "<b>" + (current + 1) + "</b> / " + slides.length;
    prevBtn.disabled = current === 0;
    nextBtn.disabled = current === slides.length - 1;

    if (push !== false) {
      history.replaceState(null, "", "#" + (current + 1));
    }
  }

  function next() { show(current + 1); }
  function prev() { show(current - 1); }

  function toggleOverview() {
    overview.classList.toggle("open");
  }

  /* ---- overview grid, built once from the slides themselves ---- */

  var grid = overview.querySelector(".grid");
  slides.forEach(function (s, n) {
    var b = document.createElement("button");
    var heading = s.querySelector("h1, h2");
    b.innerHTML =
      '<div class="i">' + String(n + 1).padStart(2, "0") + "</div>" +
      '<div class="t"></div>';
    b.querySelector(".t").textContent = heading ? heading.textContent : "—";
    b.addEventListener("click", function () {
      overview.classList.remove("open");
      show(n);
    });
    grid.appendChild(b);
  });

  prevBtn.addEventListener("click", prev);
  nextBtn.addEventListener("click", next);

  /* ---- keyboard ---- */

  document.addEventListener("keydown", function (e) {
    if (e.metaKey || e.ctrlKey || e.altKey) return;

    switch (e.key) {
      case "ArrowRight":
      case "ArrowDown":
      case "PageDown":
      case " ":
        e.preventDefault(); next(); break;
      case "ArrowLeft":
      case "ArrowUp":
      case "PageUp":
        e.preventDefault(); prev(); break;
      case "Home":
        e.preventDefault(); show(0); break;
      case "End":
        e.preventDefault(); show(slides.length - 1); break;
      case "o":
      case "O":
        e.preventDefault(); toggleOverview(); break;
      case "Escape":
        overview.classList.remove("open"); break;
      case "f":
      case "F":
        e.preventDefault();
        if (document.fullscreenElement) document.exitFullscreen();
        else document.documentElement.requestFullscreen();
        break;
    }
  });

  /* ---- click and swipe ---- */

  document.addEventListener("click", function (e) {
    if (overview.classList.contains("open")) return;
    if (e.target.closest("a, button, .term, #nav")) return;
    // Right third advances, left third goes back, middle does nothing, so a
    // stray click while presenting cannot jump the deck unpredictably.
    var x = e.clientX / window.innerWidth;
    if (x > 0.72) next();
    else if (x < 0.28) prev();
  });

  var touchX = null;
  document.addEventListener("touchstart", function (e) {
    touchX = e.changedTouches[0].clientX;
  }, { passive: true });

  document.addEventListener("touchend", function (e) {
    if (touchX === null) return;
    var dx = e.changedTouches[0].clientX - touchX;
    if (Math.abs(dx) > 60) { dx < 0 ? next() : prev(); }
    touchX = null;
  }, { passive: true });

  /* ---- boot ---- */

  var fromHash = parseInt((location.hash || "").replace("#", ""), 10);
  show(isNaN(fromHash) ? 0 : fromHash - 1, false);
})();
