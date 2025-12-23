function initStatsExit() {
  // Recherche d'articles (colonne de gauche)
  const formSearch = document.getElementById("form-search-stats");
  const qInput = document.getElementById("q-stats");
  const itemsList = document.getElementById("items-list-stats");
  const resultsCount = document.getElementById("results-count-stats");

  // Zone statistiques (colonne de droite)
  const selectedArticleP = document.getElementById("selected-article");
  const formFilterStats = document.getElementById("form-filter-stats");
  const messageP = document.getElementById("stats-message");
  const theadStatsExitYearly = document.getElementById("thead-stats-exit-yearly");
  const tbodyStatsExitYearly = document.getElementById("tbody-stats-exit-yearly");
  const theadStatsExitMonthly = document.getElementById("thead-stats-exit-monthly");
  const tbodyStatsExitMonthly = document.getElementById("tbody-stats-exit-monthly");
  const svgYearly = document.getElementById("stats-exit-chart-yearly");
  const svgMonthly = document.getElementById("stats-exit-chart-monthly");
  const exitMotifCheckboxes = document.querySelectorAll(".exit-motif-stats");

  let selectedCodeArticle = null;
  let selectedLibelle = null;

  let lastStatsYear = [];
  let lastStatsMonth = [];

  function getChartLabelColor() {
    try {
      const v = getComputedStyle(document.body).getPropertyValue("--chart-label-color");
      const c = (v || "").trim();
      return c || "#000";
    } catch (e) {
      return (document.body && document.body.classList.contains("dark-theme")) ? "#fff" : "#000";
    }
  }

  function rerenderChartsIfAny() {
    if (svgYearly && Array.isArray(lastStatsYear) && lastStatsYear.length) {
      renderYearlyBarChart(svgYearly, lastStatsYear);
    }
    if (svgMonthly && Array.isArray(lastStatsMonth) && lastStatsMonth.length) {
      renderMonthlyBarChart(svgMonthly, lastStatsMonth);
    }
  }

  function escapeHtml(str) {
    return (str == null ? "" : String(str))
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  async function searchItemsForStats() {
    const q = (qInput && qInput.value || "").trim();
    if (resultsCount) resultsCount.textContent = "";
    if (itemsList) itemsList.innerHTML = "";

    try {
      const res = await fetch(API("/items/search"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ q, filters: {}, limit: 300 }),
      });
      if (!res.ok) throw new Error("search_failed");
      const data = await res.json();
      const allCols = data.columns || [];
      const rows = data.rows || [];

      // colonnes affichées: priorité à code_article + libelle_court_article
      let cols = allCols;
      const simpleCols = [];
      if (allCols.includes("code_article")) simpleCols.push("code_article");
      if (allCols.includes("libelle_court_article")) simpleCols.push("libelle_court_article");
      if (simpleCols.length) {
        cols = simpleCols;
      }

      if (resultsCount) {
        resultsCount.textContent = rows.length ? `${rows.length} résultat(s)` : "Aucun résultat";
      }

      if (itemsList) {
        itemsList.innerHTML = "";
        rows.forEach(r => {
          const item = document.createElement("div");
          item.className = "item-row-stats";
          item.dataset.full = JSON.stringify(r);
          item.style.cursor = "pointer";
          item.style.padding = "8px";
          item.style.border = "1px solid rgba(255,255,255,0.12)";
          item.style.borderRadius = "8px";

          const codeVal = r.code_article != null ? String(r.code_article) : "";
          const libVal = r.libelle_court_article != null ? String(r.libelle_court_article) : "";
          item.innerHTML = `
            <div style="font-weight:600;">${escapeHtml(codeVal)}</div>
            <div class="muted" style="font-size:0.85rem;">${escapeHtml(libVal)}</div>
          `;

          itemsList.appendChild(item);
        });
      }
    } catch (e) {
      if (resultsCount) resultsCount.textContent = "Erreur de recherche";
    }
  }

  async function loadStatsForSelectedArticle() {
    const code = (selectedCodeArticle || "").trim();
    if (!code) {
      if (messageP) messageP.textContent = "Aucun article sélectionné.";
      return;
    }

    if (messageP) messageP.textContent = "Chargement des statistiques...";
    if (theadStatsExitYearly) theadStatsExitYearly.innerHTML = "";
    if (tbodyStatsExitYearly) tbodyStatsExitYearly.innerHTML = "";
    if (theadStatsExitMonthly) theadStatsExitMonthly.innerHTML = "";
    if (tbodyStatsExitMonthly) tbodyStatsExitMonthly.innerHTML = "";
    if (svgYearly) svgYearly.innerHTML = "";
    if (svgMonthly) svgMonthly.innerHTML = "";

    try {
      // Construire les 2 URLs : annuelle (table) et mensuelle (graph)
      const urlYear = new URL(API(`/items/${encodeURIComponent(code)}/stats-exit`));
      const urlMonth = new URL(API(`/items/${encodeURIComponent(code)}/stats-exit-monthly`));

      // 1) types de sortie via cases à cocher
      if (exitMotifCheckboxes && exitMotifCheckboxes.length) {
        exitMotifCheckboxes.forEach(cb => {
          if (cb.checked) {
            urlYear.searchParams.append("type_exit", cb.value);
            urlMonth.searchParams.append("type_exit", cb.value);
          }
        });
      }

      // Appels parallèles : annuelle + mensuelle
      const [resYear, resMonth] = await Promise.all([
        fetch(urlYear.toString()),
        fetch(urlMonth.toString()),
      ]);

      if (!resYear.ok) {
        if (messageP) messageP.textContent = `Erreur API annuelle (${resYear.status}).`;
        return;
      }
      if (!resMonth.ok) {
        if (messageP) messageP.textContent = `Erreur API mensuelle (${resMonth.status}).`;
        return;
      }

      const dataYear = await resYear.json();
      const dataMonth = await resMonth.json();

      const rowsYear = dataYear.rows || [];
      const rowsMonth = dataMonth.rows || [];

      // Tableau des stats par année (annee, qte_mvt)
      const colsYear = ["annee", "qte_mvt"];
      if (theadStatsExitYearly) {
        theadStatsExitYearly.innerHTML = colsYear.map(c => `<th>${escapeHtml(c)}</th>`).join("");
      }
      if (tbodyStatsExitYearly) {
        tbodyStatsExitYearly.innerHTML = rowsYear.map(r => {
          const annee = r.annee != null ? String(r.annee) : "";
          const qte = r.qte_mvt != null ? String(r.qte_mvt) : "0";
          return `<tr><td>${escapeHtml(annee)}</td><td>${escapeHtml(qte)}</td></tr>`;
        }).join("");
      }

      // Tableau des stats mensuelles (annee en cours, 12 mois)
      const colsMonth = ["annee", "mois", "qte_mvt"];
      if (theadStatsExitMonthly) {
        theadStatsExitMonthly.innerHTML = colsMonth.map(c => `<th>${escapeHtml(c)}</th>`).join("");
      }
      if (tbodyStatsExitMonthly) {
        tbodyStatsExitMonthly.innerHTML = rowsMonth.map(r => {
          const annee = r.annee != null ? String(r.annee) : "";
          const mois = r.mois != null ? String(r.mois) : "";
          const qte = r.qte_mvt != null ? String(r.qte_mvt) : "0";
          return `<tr><td>${escapeHtml(annee)}</td><td>${escapeHtml(mois)}</td><td>${escapeHtml(qte)}</td></tr>`;
        }).join("");
      }

      // Données pour graph annuel
      const statsYear = rowsYear.map(r => ({
        annee: +r.annee,
        qte_mvt: +r.qte_mvt,
      })).filter(d => !Number.isNaN(d.annee) && !Number.isNaN(d.qte_mvt));

      // Données pour graph mensuel (annee en cours, 12 mois)
      const statsMonth = rowsMonth.map(r => ({
        annee: +r.annee,
        mois: +r.mois,
        qte_mvt: +r.qte_mvt,
      })).filter(d => !Number.isNaN(d.annee) && !Number.isNaN(d.mois) && !Number.isNaN(d.qte_mvt));

      lastStatsYear = statsYear;
      lastStatsMonth = statsMonth;

      if (!statsYear.length && !statsMonth.length) {
        if (messageP) messageP.textContent = "Aucune donnée de sortie trouvée pour cet article (et ce filtre).";
        return;
      }

      if (messageP) {
        const lib = selectedLibelle ? ` - ${selectedLibelle}` : "";
        messageP.textContent = "";
        messageP.textContent = `Statistiques annuelles et mensuelles chargées pour l'article ${code}${lib}.`;
      }

      if (statsYear.length && svgYearly) {
        renderYearlyBarChart(svgYearly, statsYear);
      }
      if (statsMonth.length && svgMonthly) {
        renderMonthlyBarChart(svgMonthly, statsMonth);
      }
    } catch (e) {
      if (messageP) messageP.textContent = "Erreur lors du chargement des statistiques.";
    }
  }

  function renderYearlyBarChart(svgElement, data) {
    if (!svgElement || typeof d3 === "undefined") return;
    svgElement.innerHTML = "";

    const svg = d3.select(svgElement);
    const bbox = svgElement.getBoundingClientRect ? svgElement.getBoundingClientRect() : { width: 0, height: 0 };
    const width = (+svg.attr("width") || bbox.width || 800);
    const height = (+svg.attr("height") || bbox.height || 360);
    const margin = { top: 20, right: 20, bottom: 40, left: 60 };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;

    const g = svg.append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);

    const x = d3.scaleBand()
      .domain(data.map(d => d.annee))
      .range([0, innerWidth])
      .padding(0.1);

    const labelColor = getChartLabelColor();

    const yExtent = d3.extent(data, d => d.qte_mvt);
    const yMinVal = (yExtent && yExtent[0] != null) ? yExtent[0] : 0;
    const yMaxVal = (yExtent && yExtent[1] != null) ? yExtent[1] : 0;
    const yPad = Math.max(1, (yMaxVal - yMinVal) * 0.1);

    const y = d3.scaleLinear()
      .domain(yMinVal === yMaxVal ? [yMinVal - 1, yMaxVal + 1] : [yMinVal - yPad, yMaxVal + yPad])
      .range([innerHeight, 0])
      .nice();

    g.selectAll(".bar")
      .data(data, d => d.annee)
      .enter()
      .append("rect")
      .attr("class", "bar")
      .attr("x", d => x(d.annee))
      .attr("y", d => y(d.qte_mvt))
      .attr("width", x.bandwidth())
      .attr("height", d => innerHeight - y(d.qte_mvt))
      .attr("fill", "steelblue");

    g.selectAll(".bar-label")
      .data(data, d => d.annee)
      .enter()
      .append("text")
      .attr("class", "bar-label")
      .attr("x", d => (x(d.annee) || 0) + x.bandwidth() / 2)
      .attr("y", d => {
        const yTop = y(d.qte_mvt) - 4;
        // Si le label dépasse en haut du graphique, on le place dans la barre.
        // (g est déjà translaté, donc 0 = haut du chart interne)
        return yTop < 10 ? (y(d.qte_mvt) + 12) : yTop;
      })
      .attr("text-anchor", "middle")
      .attr("font-size", "10px")
      .attr("fill", labelColor)
      .text(d => d.qte_mvt);

    g.append("g")
      .attr("transform", `translate(0,${innerHeight})`)
      .call(d3.axisBottom(x).tickFormat(d3.format("d")));

    g.append("g")
      .call(d3.axisLeft(y));
  }


  function renderMonthlyBarChart(svgElement, data) {
    if (!svgElement || typeof d3 === "undefined") return;
    svgElement.innerHTML = "";

    const svg = d3.select(svgElement);
    const bbox = svgElement.getBoundingClientRect ? svgElement.getBoundingClientRect() : { width: 0, height: 0 };
    const width = (+svg.attr("width") || bbox.width || 800);
    const height = (+svg.attr("height") || bbox.height || 360);
    const margin = { top: 20, right: 20, bottom: 40, left: 60 };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;

    const g = svg.append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);

    // Domain X = 12 mois (1..12) même si data en a moins
    const allMonths = d3.range(1, 13);
    const monthLabels = ["Jan", "Fév", "Mar", "Avr", "Mai", "Jun", "Jul", "Aoû", "Sep", "Oct", "Nov", "Déc"];

    const x = d3.scaleBand()
      .domain(allMonths)
      .range([0, innerWidth])
      .padding(0.1);

    const labelColor = getChartLabelColor();

    const yExtent = d3.extent(data, d => d.qte_mvt);
    const yMinVal = (yExtent && yExtent[0] != null) ? yExtent[0] : 0;
    const yMaxVal = (yExtent && yExtent[1] != null) ? yExtent[1] : 0;
    const yPad = Math.max(1, (yMaxVal - yMinVal) * 0.1);

    const y = d3.scaleLinear()
      .domain(yMinVal === yMaxVal ? [yMinVal - 1, yMaxVal + 1] : [yMinVal - yPad, yMaxVal + yPad])
      .range([innerHeight, 0])
      .nice();

    g.selectAll(".bar")
      .data(data, d => d.mois)
      .enter()
      .append("rect")
      .attr("class", "bar")
      .attr("x", d => x(d.mois))
      .attr("y", d => y(d.qte_mvt))
      .attr("width", x.bandwidth())
      .attr("height", d => innerHeight - y(d.qte_mvt))
      .attr("fill", "steelblue");

    g.selectAll(".bar-label")
      .data(data, d => d.mois)
      .enter()
      .append("text")
      .attr("class", "bar-label")
      .attr("x", d => (x(d.mois) || 0) + x.bandwidth() / 2)
      .attr("y", d => {
        const yTop = y(d.qte_mvt) - 4;
        return yTop < 10 ? (y(d.qte_mvt) + 12) : yTop;
      })
      .attr("text-anchor", "middle")
      .attr("font-size", "10px")
      .attr("fill", labelColor)
      .text(d => d.qte_mvt);

    g.append("g")
      .attr("transform", `translate(0,${innerHeight})`)
      .call(d3.axisBottom(x).tickFormat(m => monthLabels[m - 1] || String(m)));

    g.append("g")
      .call(d3.axisLeft(y));
  }

  // Events
  if (formSearch) {
    formSearch.addEventListener("submit", (ev) => {
      ev.preventDefault();
      searchItemsForStats();
    });
  }

  if (itemsList) {
    itemsList.addEventListener("click", (ev) => {
      const item = ev.target && ev.target.closest ? ev.target.closest(".item-row-stats") : null;
      if (!item) return;

      if (itemsList) {
        itemsList.querySelectorAll(".item-row-stats").forEach(row => row.style.background = "");
        item.style.background = "rgba(255,255,255,0.06)";
      }

      let full = {};
      try { full = JSON.parse(item.dataset.full || "{}"); } catch (e) { full = {}; }

      selectedCodeArticle = (full.code_article || full.code || full.id_article || "").toString();
      selectedLibelle = full.libelle_court_article || "";

      if (selectedArticleP) {
        const libPart = selectedLibelle ? ` - ${selectedLibelle}` : "";
        selectedArticleP.textContent = `Article sélectionné : ${selectedCodeArticle}${libPart}`;
      }

      loadStatsForSelectedArticle();
    });
  }

  if (formFilterStats) {
    formFilterStats.addEventListener("submit", (ev) => {
      ev.preventDefault();
      loadStatsForSelectedArticle();
    });
  }

  if (exitMotifCheckboxes && exitMotifCheckboxes.length) {
    exitMotifCheckboxes.forEach(cb => {
      cb.addEventListener("change", () => {
        loadStatsForSelectedArticle();
      });
    });
  }

  // Initialisation avec paramètre ?code=... pour ouvrir directement un article
  (async () => {
    try {
      const url = new URL(window.location.href);
      const codeParam = (
        url.searchParams.get("code") ||
        url.searchParams.get("code_article") ||
        url.searchParams.get("codeArticle") ||
        ""
      ).trim();
      if (!codeParam) return;

      selectedCodeArticle = codeParam;
      selectedLibelle = "";
      if (selectedArticleP) {
        selectedArticleP.textContent = `Article sélectionné : ${selectedCodeArticle}`;
      }
      await loadStatsForSelectedArticle();
    } catch (e) {
      // ignore erreur d'URL
    }
  })();

  // Re-render des graphes quand le thème change (ex: passage en mode sombre)
  try {
    if (window.MutationObserver && document.body) {
      const obs = new MutationObserver((mutations) => {
        for (const m of mutations) {
          if (m.type === "attributes" && m.attributeName === "class") {
            rerenderChartsIfAny();
            break;
          }
        }
      });
      obs.observe(document.body, { attributes: true, attributeFilter: ["class"] });
    }
  } catch (e) {
    // ignore
  }
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initStatsExit);
} else {
  initStatsExit();
}
