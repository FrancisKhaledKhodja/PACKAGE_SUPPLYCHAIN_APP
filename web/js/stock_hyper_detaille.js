document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("form-search-stock-hyper");
  const qInput = document.getElementById("q-stock-hyper");
  const btn = document.getElementById("btn-search-stock-hyper");

  const resultsCount = document.getElementById("results-count-stock-hyper");
  const theadItems = document.getElementById("thead-row-items-stock-hyper");
  const tbodyItems = document.getElementById("tbody-rows-items-stock-hyper");

  const theadStock = document.getElementById("thead-row-stock-hyper");
  const tbodyStock = document.getElementById("tbody-rows-stock-hyper");
  const stockMeta = document.getElementById("stock-hyper-meta");

  const filterCodeMagasin = document.getElementById("filter-code-magasin-hyper");
  const filterTypeDepot = document.getElementById("filter-type-depot-hyper");
  const filterQualite = document.getElementById("filter-qualite-hyper");
  const filterFlagDM = document.getElementById("filter-flag-dm-hyper");
  const btnExportCsv = document.getElementById("btn-export-stock-hyper-csv");

  let currentStockRows = [];

  function getCategorieSansSortieColor(value) {
    const v = (value || "").trim();
    switch (v) {
      case "1 - moins de 2 mois":
        return "#33CC00";
      case "2 - entre 2 et 6 mois":
        return "#66AA00";
      case "3 - entre 6 mois et 1 an":
        return "#999900";
      case "4 - entre 1 et 2 ans":
        return "#CC6600";
      case "5 - entre 2 et 5 ans":
        return "#FF3300";
      case "6 - entre 5 et 10 ans":
        return "#FF0000";
      default:
        return "#FF0000";
    }
  }

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
          loadStockHyperForArticle(code, r.libelle_court_article || "");
        }
      });
      tbodyItems.appendChild(tr);
    });
  }

  function renderStockHyperTable(rows) {
    if (!theadStock || !tbodyStock) return;
    theadStock.innerHTML = "";
    tbodyStock.innerHTML = "";

    if (!rows.length) return;

    const first = rows[0] || {};
    const cols = [
      "code_magasin",
      "libelle_magasin",
      "type_de_depot",
      "flag_stock_d_m",
      "emplacement",
      "code_article",
      "libelle_court_article",
      "n_lot",
      "n_serie",
      "qte_stock",
      "qualite",
      "n_colis_aller",
      "n_colis_retour",
      "n_cde_dpm_dpi",
      "demandeur_dpi",
      "code_projet",
      "libelle_projet",
      "statut_projet",
      "responsable_projet",
      "date_reception_corrigee",
      "categorie_anciennete",
      "categorie_sans_sortie",
      "bu",
      "date_stock",
    ].filter(c => Object.prototype.hasOwnProperty.call(first, c));

    theadStock.innerHTML = cols.map(c => `<th>${c}</th>`).join("");

    rows.forEach(r => {
      const tr = document.createElement("tr");
      cols.forEach(c => {
        const td = document.createElement("td");
        const raw = r[c];
        const text = raw != null ? String(raw) : "";

        if (c === "categorie_sans_sortie" || c === "categorie_anciennete_stock" || c === "categorie_anciennete") {
          const color = getCategorieSansSortieColor(text);
          td.style.backgroundColor = color;
          td.style.color = "#000";
          td.style.padding = "2px 4px";
          td.textContent = text;
        } else {
          td.textContent = text;
        }

        tr.appendChild(td);
      });
      tbodyStock.appendChild(tr);
    });
  }

  function applyStockFilters() {
    const filtered = getFilteredRows();
    renderStockHyperTable(filtered);
  }

  function getFilteredRows() {
    if (!currentStockRows || !currentStockRows.length) {
      return [];
    }

    const codeMagasin = (filterCodeMagasin && filterCodeMagasin.value || "").trim().toLowerCase();
    const typeDepot = (filterTypeDepot && filterTypeDepot.value || "").trim().toLowerCase();
    const qualite = (filterQualite && filterQualite.value || "").trim().toLowerCase();
    const flagDM = (filterFlagDM && filterFlagDM.value || "").trim().toLowerCase();

    return currentStockRows.filter(r => {
      if (codeMagasin && String(r.code_magasin || "").toLowerCase().indexOf(codeMagasin) === -1) return false;
      if (typeDepot && String(r.type_de_depot || "").toLowerCase().indexOf(typeDepot) === -1) return false;
      if (qualite && String(r.qualite || "").toLowerCase().indexOf(qualite) === -1) return false;
      if (flagDM && String(r.flag_stock_d_m || "").toLowerCase().indexOf(flagDM) === -1) return false;
      return true;
    });
  }

  function exportCurrentStockToCsv() {
    const rows = getFilteredRows();
    if (!rows.length) {
      alert("Aucune ligne à exporter (vérifiez les filtres et le stock chargé).");
      return;
    }

    const first = rows[0] || {};
    const cols = [
      "code_magasin",
      "libelle_magasin",
      "type_de_depot",
      "flag_stock_d_m",
      "emplacement",
      "code_article",
      "libelle_court_article",
      "n_lot",
      "n_serie",
      "qte_stock",
      "qualite",
      "n_colis_aller",
      "n_colis_retour",
      "n_cde_dpm_dpi",
      "demandeur_dpi",
      "code_projet",
      "libelle_projet",
      "statut_projet",
      "responsable_projet",
      "date_reception_corrigee",
      "categorie_anciennete",
      "categorie_sans_sortie",
      "bu",
      "date_stock",
    ].filter(c => Object.prototype.hasOwnProperty.call(first, c));

    const escapeCell = (val) => {
      if (val == null) return "";
      const str = String(val);
      // on échappe guillemets et on entoure si besoin
      const escaped = str.replace(/"/g, '""');
      if (escaped.indexOf(";") !== -1 || escaped.indexOf("\n") !== -1 || escaped.indexOf("\r") !== -1) {
        return `"${escaped}"`;
      }
      return escaped;
    };

    const lines = [];
    lines.push(cols.join(";"));
    rows.forEach(r => {
      const line = cols.map(c => escapeCell(r[c])).join(";");
      lines.push(line);
    });

    const csvContent = lines.join("\r\n");
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);

    const a = document.createElement("a");
    a.href = url;
    a.download = "stock_hyper_detaille.csv";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
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

  async function loadStockHyperForArticle(code, libelle) {
    if (!code) return;
    if (theadStock) theadStock.innerHTML = "";
    if (tbodyStock) tbodyStock.innerHTML = "";
    if (stockMeta) stockMeta.textContent = `Chargement du stock hyper détaillé pour ${code}...`;

    try {
      const res = await fetch(API(`/auth/stock/${encodeURIComponent(code)}/ultra-details`));
      if (!res.ok) {
        if (stockMeta) stockMeta.textContent = `Erreur API stock hyper détaillé (${res.status})`;
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
      if (stockMeta) stockMeta.textContent = "Erreur de communication avec l'API stock hyper détaillé";
    }
  }

  if (form) {
    form.addEventListener("submit", (ev) => {
      ev.preventDefault();
      searchItems();
    });
  }

  [filterCodeMagasin, filterTypeDepot, filterQualite, filterFlagDM].forEach(input => {
    if (!input) return;
    input.addEventListener("input", () => {
      applyStockFilters();
    });
  });
  if (btnExportCsv) {
    btnExportCsv.addEventListener("click", () => {
      exportCurrentStockToCsv();
    });
  }
  if (btn) {
    btn.addEventListener("click", (ev) => {
      ev.preventDefault();
      searchItems();
    });
  }

  (async () => {
    try {
      const url = new URL(window.location.href);
      const codeParam = (url.searchParams.get("code") || "").trim();
      if (!codeParam) return;

      if (qInput) qInput.value = codeParam;
      await loadStockHyperForArticle(codeParam, "");
    } catch (e) {
    }
  })();
});
