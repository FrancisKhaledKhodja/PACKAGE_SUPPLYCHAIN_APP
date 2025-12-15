document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("form-search-stock-detailed");
  const qInput = document.getElementById("q-stock-detailed");
  const btn = document.getElementById("btn-search-stock-detailed");

  const resultsCount = document.getElementById("results-count-stock-detailed");
  const theadItems = document.getElementById("thead-row-items-stock-detailed");
  const tbodyItems = document.getElementById("tbody-rows-items-stock-detailed");

  const theadStock = document.getElementById("thead-row-stock-detailed");
  const tbodyStock = document.getElementById("tbody-rows-stock-detailed");
  const stockMeta = document.getElementById("stock-detailed-meta");

  const filterCodeMagasin = document.getElementById("filter-code-magasin");
  const filterTypeDepot = document.getElementById("filter-type-depot");
  const filterFlagDM = document.getElementById("filter-flag-dm");
  const filterCodeQualite = document.getElementById("filter-code-qualite");

  let currentStockRows = [];

  function renderItemsTable(rows, columns) {
    if (!theadItems || !tbodyItems) return;
    theadItems.innerHTML = "";
    tbodyItems.innerHTML = "";

    let cols = columns || [];
    const simpleCols = [];
    if (cols.includes("code_article")) simpleCols.push("code_article");
    if (cols.includes("libelle_court_article")) simpleCols.push("libelle_court_article");
    if (simpleCols.length) {
      cols = simpleCols;
    }

    theadItems.innerHTML = cols.map(c => `<th>${c}</th>`).join("");

    rows.forEach(r => {
      const tr = document.createElement("tr");
      tr.className = "item-row";
      tr.dataset.codeArticle = r.code_article || "";
      cols.forEach(c => {
        const td = document.createElement("td");
        td.textContent = r[c] != null ? String(r[c]) : "";
        tr.appendChild(td);
      });
      tr.addEventListener("click", () => {
        const code = tr.dataset.codeArticle;
        if (code) {
          loadStockDetailsForArticle(code, r.libelle_court_article || "");
        }
      });
      tbodyItems.appendChild(tr);
    });
  }

  function renderStockDetailsTable(rows) {
    if (!theadStock || !tbodyStock) return;
    theadStock.innerHTML = "";
    tbodyStock.innerHTML = "";

    if (!rows.length) return;

    const first = rows[0] || {};
    const cols = [
      "code_magasin",
      "libelle_magasin",
      "type_de_depot",
      "emplacement",
      "flag_stock_d_m",
      "code_qualite",
      "qte_stock",
    ].filter(c => Object.prototype.hasOwnProperty.call(first, c));

    theadStock.innerHTML = cols.map(c => `<th>${c}</th>`).join("");

    rows.forEach(r => {
      const tr = document.createElement("tr");
      cols.forEach(c => {
        const td = document.createElement("td");
        td.textContent = r[c] != null ? String(r[c]) : "";
        tr.appendChild(td);
      });
      tbodyStock.appendChild(tr);
    });
  }

  function applyStockFilters() {
    if (!currentStockRows || !currentStockRows.length) {
      renderStockDetailsTable([]);
      if (stockMeta && stockMeta.textContent) {
        // on laisse le texte, juste tableau vide
      }
      return;
    }

    const codeMagasin = (filterCodeMagasin && filterCodeMagasin.value || "").trim().toLowerCase();
    const typeDepot = (filterTypeDepot && filterTypeDepot.value || "").trim().toLowerCase();
    const flagDM = (filterFlagDM && filterFlagDM.value || "").trim().toLowerCase();
    const codeQualite = (filterCodeQualite && filterCodeQualite.value || "").trim().toLowerCase();

    const filtered = currentStockRows.filter(r => {
      if (codeMagasin && String(r.code_magasin || "").toLowerCase().indexOf(codeMagasin) === -1) return false;
      if (typeDepot && String(r.type_de_depot || "").toLowerCase().indexOf(typeDepot) === -1) return false;
      if (flagDM && String(r.flag_stock_d_m || "").toLowerCase().indexOf(flagDM) === -1) return false;
      if (codeQualite && String(r.code_qualite || "").toLowerCase().indexOf(codeQualite) === -1) return false;
      return true;
    });

    renderStockDetailsTable(filtered);
  }

  async function searchItems() {
    const q = (qInput && qInput.value || "").trim();

    if (theadItems) theadItems.innerHTML = "";
    if (tbodyItems) tbodyItems.innerHTML = "";
    if (resultsCount) resultsCount.textContent = "";

    if (!q) {
      if (resultsCount) resultsCount.textContent = "Veuillez saisir un terme de recherche";
      return;
    }

    try {
      const res = await fetch(API("/items/search"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ q, filters: {}, limit: 300 }),
      });
      if (!res.ok) {
        if (resultsCount) resultsCount.textContent = `Erreur API items (${res.status})`;
        return;
      }
      const data = await res.json();
      const cols = data.columns || [];
      const rows = data.rows || [];

      if (resultsCount) {
        resultsCount.textContent = rows.length ? `${rows.length} résultat(s)` : "Aucun résultat";
      }

      renderItemsTable(rows, cols);
    } catch (e) {
      if (resultsCount) resultsCount.textContent = "Erreur de communication avec l'API items";
    }
  }

  async function loadStockDetailsForArticle(code, libelle) {
    if (!code) return;
    if (theadStock) theadStock.innerHTML = "";
    if (tbodyStock) tbodyStock.innerHTML = "";
    if (stockMeta) stockMeta.textContent = `Chargement du stock détaillé pour ${code}...`;

    try {
      const res = await fetch(API(`/auth/stock/${encodeURIComponent(code)}/details`));
      if (!res.ok) {
        if (stockMeta) stockMeta.textContent = `Erreur API stock détaillé (${res.status})`;
        return;
      }
      const data = await res.json();
      const rows = data.rows || [];

      currentStockRows = rows;

      if (stockMeta) {
        const total = currentStockRows.reduce((acc, r) => acc + (Number(r.qte_stock) || 0), 0);
        const label = libelle ? ` - ${libelle}` : "";
        stockMeta.textContent = currentStockRows.length
          ? `${rows.length} ligne(s) de stock pour ${code}${label} – Quantité totale: ${total}`
          : `Aucun stock trouvé pour ${code}${label}`;
      }

      applyStockFilters();
    } catch (e) {
      if (stockMeta) stockMeta.textContent = "Erreur de communication avec l'API stock détaillé";
    }
  }

  if (form) {
    form.addEventListener("submit", (ev) => {
      ev.preventDefault();
      searchItems();
    });
  }

  [filterCodeMagasin, filterTypeDepot, filterFlagDM, filterCodeQualite].forEach(input => {
    if (!input) return;
    input.addEventListener("input", () => {
      applyStockFilters();
    });
  });
  if (btn) {
    btn.addEventListener("click", (ev) => {
      ev.preventDefault();
      searchItems();
    });
  }

  // Initialisation avec paramètre ?code=... pour ouvrir directement le stock détaillé
  (async () => {
    try {
      const url = new URL(window.location.href);
      const codeParam = (url.searchParams.get("code") || "").trim();
      if (!codeParam) return;

      if (qInput) qInput.value = codeParam;
      // on tente de charger directement le stock détaillé
      await loadStockDetailsForArticle(codeParam, "");
    } catch (e) {
      // ignore erreur d'URL
    }
  })();
});
