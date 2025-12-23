(function () {
  function loadScript(src, onload, onerror) {
    var s = document.createElement("script");
    s.src = src;
    s.defer = true;
    s.onload = onload;
    s.onerror = onerror;
    document.head.appendChild(s);
  }

  function hasD3() {
    return typeof window.d3 !== "undefined";
  }

  function showD3Error() {
    try {
      var el = document.getElementById("stats-message");
      if (el) {
        el.textContent = "Impossible de charger D3.js (offline/CDN). Déposez le fichier web/js/vendor/d3.v7.min.js ou rétablissez l'accès Internet.";
      }
    } catch (e) {
      /* ignore */
    }
  }

  function loadStatsExit() {
    loadScript("js/stats_exit.js?v=1", function () {}, function () {});
  }

  // Déjà présent (cas d'un bundle ou d'un cache navigateur)
  if (hasD3()) {
    loadStatsExit();
    return;
  }

  // 1) Essai local (offline-friendly)
  loadScript("js/vendor/d3.v7.min.js", function () {
    if (hasD3()) {
      loadStatsExit();
      return;
    }
    // Local chargé mais D3 absent => fallback CDN
    loadScript("https://d3js.org/d3.v7.min.js", function () {
      if (hasD3()) {
        loadStatsExit();
        return;
      }
      showD3Error();
    }, showD3Error);
  }, function () {
    // 2) Fallback CDN
    loadScript("https://d3js.org/d3.v7.min.js", function () {
      if (hasD3()) {
        loadStatsExit();
        return;
      }
      showD3Error();
    }, showD3Error);
  });
})();
