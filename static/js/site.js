/* Maison Riri Design — interactions légères, sans dépendance. */
(function () {
  "use strict";

  // Menu mobile
  var burger = document.querySelector("[data-burger]");
  var nav = document.getElementById("primary-nav");
  if (burger && nav) {
    burger.addEventListener("click", function () {
      var open = burger.getAttribute("aria-expanded") === "true";
      burger.setAttribute("aria-expanded", String(!open));
      nav.classList.toggle("is-open", !open);
    });
    nav.addEventListener("click", function (event) {
      if (event.target.closest("a")) {
        burger.setAttribute("aria-expanded", "false");
        nav.classList.remove("is-open");
      }
    });
  }

  // Filet sous l'en-tête dès que la page défile
  var masthead = document.querySelector("[data-masthead]");
  if (masthead) {
    var onScroll = function () {
      masthead.classList.toggle("is-scrolled", window.scrollY > 12);
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
  }

  // Apparitions au défilement
  var reveals = document.querySelectorAll(".reveal");
  if (!("IntersectionObserver" in window)) {
    reveals.forEach(function (el) { el.classList.add("is-visible"); });
  } else {
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          observer.unobserve(entry.target);
        }
      });
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.08 });
    reveals.forEach(function (el) { observer.observe(el); });
  }

  // Récapitulatif des photos d'inspiration sélectionnées
  var fileInput = document.querySelector('input[type="file"][multiple]');
  if (fileInput) {
    var summary = document.createElement("p");
    summary.className = "file-list";
    fileInput.insertAdjacentElement("afterend", summary);
    fileInput.addEventListener("change", function () {
      var names = Array.prototype.map.call(fileInput.files, function (f) { return f.name; });
      summary.textContent = names.length ? names.join(" · ") : "";
    });
  }
})();
