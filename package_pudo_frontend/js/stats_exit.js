document.addEventListener("DOMContentLoaded", () => {
  // Recherche d'articles (colonne de gauche)
  const formSearch = document.getElementById("form-search-stats");
  const qInput = document.getElementById("q-stats");
  const theadItems = document.getElementById("thead-stats");
  const tbodyItems = document.getElementById("tbody-stats");
  const resultsCount = document.getElementById("results-count-stats");

  // Zone statistiques (colonne de droite)
  const selectedArticleP = document.getElementById("selected-article");
  const formFilterStats = document.getElementById("form-filter-stats");
  const typeExitInput = document.getElementById("type-exit");
  const messageP = document.getElementById("stats-message");
  const theadStatsExit = document.getElementById("thead-stats-exit");
  const tbodyStatsExit = document.getElementById("tbody-stats-exit");
  const svgEl = document.getElementById("stats-exit-chart");
  const exitMotifCheckboxes = document.querySelectorAll(".exit-motif-stats");

  let selectedCodeArticle = null;
  let selectedLibelle = null;

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
    if (theadItems) theadItems.innerHTML = "";
    if (tbodyItems) tbodyItems.innerHTML = "";

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

      if (theadItems) {
        theadItems.innerHTML = cols.map(c => `<th>${escapeHtml(c)}</th>`).join("");
      }

      if (tbodyItems) {
        tbodyItems.innerHTML = "";
        rows.forEach(r => {
          const tr = document.createElement("tr");
          tr.className = "item-row-stats";
          tr.dataset.full = JSON.stringify(r);
          cols.forEach(c => {
            const td = document.createElement("td");
            td.textContent = r[c] != null ? String(r[c]) : "";
            tr.appendChild(td);
          });
          tbodyItems.appendChild(tr);
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

    const typeExitRaw = (typeExitInput && typeExitInput.value || "").trim();

    if (messageP) messageP.textContent = "Chargement des statistiques...";
    if (theadStatsExit) theadStatsExit.innerHTML = "";
    if (tbodyStatsExit) tbodyStatsExit.innerHTML = "";
    if (svgEl) svgEl.innerHTML = "";

    try {
      const url = new URL(API(`/items/${encodeURIComponent(code)}/stats-exit`));

      // 1) types de sortie via cases à cocher
      if (exitMotifCheckboxes && exitMotifCheckboxes.length) {
        exitMotifCheckboxes.forEach(cb => {
          if (cb.checked) {
            url.searchParams.append("type_exit", cb.value);
          }
        });
      }

      // 2) filtre libre additionnel (séparé par virgules)
      if (typeExitRaw) {
        typeExitRaw.split(",").map(s => s.trim()).filter(Boolean).forEach(v => {
          url.searchParams.append("type_exit", v);
        });
      }

      const res = await fetch(url.toString());
      if (!res.ok) {
        if (messageP) messageP.textContent = `Erreur API (${res.status}).`;
        return;
      }

      const data = await res.json();
      const rows = data.rows || [];

      // Tableau des stats (annee, qte_mvt)
      const cols = ["annee", "qte_mvt"];
      if (theadStatsExit) {
        theadStatsExit.innerHTML = cols.map(c => `<th>${escapeHtml(c)}</th>`).join("");
      }
      if (tbodyStatsExit) {
        tbodyStatsExit.innerHTML = rows.map(r => {
          const annee = r.annee != null ? String(r.annee) : "";
          const qte = r.qte_mvt != null ? String(r.qte_mvt) : "";
          return `<tr><td>${escapeHtml(annee)}</td><td>${escapeHtml(qte)}</td></tr>`;
        }).join("");
      }

      const stats = rows.map(r => ({
        annee: +r.annee,
        qte_mvt: +r.qte_mvt,
      })).filter(d => !Number.isNaN(d.annee) && !Number.isNaN(d.qte_mvt));

      if (!stats.length) {
        if (messageP) messageP.textContent = "Aucune donnée de sortie trouvée pour cet article (et ce filtre).";
        return;
      }

      if (messageP) {
        const lib = selectedLibelle ? ` - ${selectedLibelle}` : "";
        messageP.textContent = `Statistiques chargées pour l'article ${code}${lib}.`;
      }

      renderBarChart(stats);
    } catch (e) {
      if (messageP) messageP.textContent = "Erreur lors du chargement des statistiques.";
    }
  }

  function renderBarChart(data) {
    if (!svgEl || typeof d3 === "undefined") return;
    svgEl.innerHTML = "";

    const svg = d3.select(svgEl);
    const width = +svg.attr("width");
    const height = +svg.attr("height");
    const margin = { top: 20, right: 20, bottom: 40, left: 60 };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;

    const g = svg.append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);

    const x = d3.scaleBand()
      .domain(data.map(d => d.annee))
      .range([0, innerWidth])
      .padding(0.1);

    const y = d3.scaleLinear()
      .domain([0, d3.max(data, d => d.qte_mvt) || 0])
      .range([innerHeight, 0])
      .nice();

    const bars = g.selectAll(".bar")
      .data(data, d => d.annee)
      .enter()
      .append("rect")
      .attr("class", "bar")
      .attr("x", d => x(d.annee))
      .attr("y", d => y(d.qte_mvt))
      .attr("width", x.bandwidth())
      .attr("height", d => innerHeight - y(d.qte_mvt))
      .attr("fill", "steelblue");

    // Labels au-dessus des barres
    g.selectAll(".bar-label")
      .data(data, d => d.annee)
      .enter()
      .append("text")
      .attr("class", "bar-label")
      .attr("x", d => (x(d.annee) || 0) + x.bandwidth() / 2)
      .attr("y", d => y(d.qte_mvt) - 4)
      .attr("text-anchor", "middle")
      .attr("font-size", "10px")
      .attr("fill", "#fff")
      .text(d => d.qte_mvt);

    g.append("g")
      .attr("transform", `translate(0,${innerHeight})`)
      .call(d3.axisBottom(x).tickFormat(d3.format("d")));

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

  if (tbodyItems) {
    tbodyItems.addEventListener("click", (ev) => {
      let tr = ev.target;
      while (tr && tr.tagName !== "TR") tr = tr.parentElement;
      if (!tr || !tr.classList.contains("item-row-stats")) return;

      if (tbodyItems) {
        tbodyItems.querySelectorAll("tr").forEach(row => row.style.background = "");
        tr.style.background = "rgba(255,255,255,0.06)";
      }

      let full = {};
      try { full = JSON.parse(tr.dataset.full || "{}"); } catch (e) { full = {}; }

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
      const codeParam = (url.searchParams.get("code") || "").trim();
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
});
