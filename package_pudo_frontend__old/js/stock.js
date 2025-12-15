document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("form-search-stock");
  const qInput = document.getElementById("q-stock");
  const btn = document.getElementById("btn-search-stock");

  const resultsCount = document.getElementById("results-count-stock");
  const theadItems = document.getElementById("thead-row-items-stock");
  const tbodyItems = document.getElementById("tbody-rows-items-stock");

  const theadStock = document.getElementById("thead-row-stock");
  const tbodyStock = document.getElementById("tbody-rows-stock");
  const stockSummaryLinkWrapper = document.getElementById("stock-summary-link-wrapper");

  const summaryDiv = document.getElementById("item-summary");
  const itemLinkWrapper = document.getElementById("item-link-wrapper");
  const photosLinkWrapper = document.getElementById("photos-link-wrapper");
  const heliosSummaryDiv = document.getElementById("helios-summary");
  const heliosLinkWrapper = document.getElementById("helios-link-wrapper");
  const exitStatsContainer = document.getElementById("exit-stats-container");
  const exitStatsLinkWrapper = document.getElementById("exit-stats-link-wrapper");
  const exitMotifCheckboxes = document.querySelectorAll(".exit-motif");

  let currentItemCode = null;

  function renderItemSummary(row) {
    if (!summaryDiv) return;
    if (!row) {
      summaryDiv.textContent = "";
      if (itemLinkWrapper) itemLinkWrapper.innerHTML = "";
      if (photosLinkWrapper) photosLinkWrapper.innerHTML = "";
      return;
    }

    const fields = [
      { label: "code_article", key: "code_article" },
      { label: "libelle_court_article", key: "libelle_court_article" },
      { label: "libelle_long_article", key: "libelle_long_article" },
      { label: "role_responsable_et_equipe", key: "role_responsable_et_equipe" },
      { label: "statut_abrege_article", key: "statut_abrege_article" },
      { label: "cycle_de_vie_de_production", key: "cycle_de_vie_de_production" },
      { label: "criticite_pim", key: "criticite_pim" },
      { label: "type_article", key: "type_article" },
      { label: "suivi_par_num_serie_oui_nc", key: "suivi_par_num_serie_oui_nc" },
      { label: "description_lieu_de_reparation", key: "description_lieu_de_reparation" },
      { label: "lieu_de_reparation_pim", key: "lieu_de_reparation_pim" },
    ];

    let html = "<table style='width:100%; border-collapse:collapse;'>";
    fields.forEach(f => {
      if (row[f.key] != null && row[f.key] !== "") {
        html += `<tr><td style="padding:2px 4px; font-weight:500;">${f.label}</td><td style="padding:2px 4px;">${row[f.key]}</td></tr>`;
      }
    });
    html += "</table>";
    summaryDiv.innerHTML = html;

    if (itemLinkWrapper) {
      const code = row.code_article || "";
      if (code) {
        const url = `items.html?code=${encodeURIComponent(code)}`;
        itemLinkWrapper.innerHTML = `<a href="${url}" target="_blank" rel="noopener noreferrer">Voir le détail complet de l'article dans l'onglet Items</a>`;
      } else {
        itemLinkWrapper.innerHTML = "";
      }
    }
  }

  async function updatePhotosLink(code) {
    if (!photosLinkWrapper) return;
    photosLinkWrapper.innerHTML = "";
    if (!code) return;

    try {
      const res = await fetch(API(`/auth/photos/${encodeURIComponent(code)}`));
      if (!res.ok) return;
      const data = await res.json();
      const files = data.files || [];
      if (!files.length) return;

      const url = `photos.html?code=${encodeURIComponent(code)}`;
      photosLinkWrapper.innerHTML = `<a href="${url}" target="_blank" rel="noopener noreferrer">Voir les photos de l'article</a>`;
    } catch (e) {
      // en cas d'erreur, on n'affiche rien
    }
  }

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

  async function loadCategorieSansSortie(code) {
    if (!code || !summaryDiv) return;
    try {
      const res = await fetch(API(`/items/${encodeURIComponent(code)}/categorie-sans-sortie`));
      if (!res.ok) return;
      const data = await res.json();
      const val = data && data.categorie_sans_sortie != null ? String(data.categorie_sans_sortie) : "";
      if (!val) return;
      const color = getCategorieSansSortieColor(val);
      const infoDiv = document.createElement("div");
      infoDiv.style.marginTop = "4px";
      infoDiv.innerHTML = `<span style="font-weight:500; margin-right:4px;">categorie_sans_sortie</span><span style="background-color:${color}; color:#000; padding:2px 6px; border-radius:4px; display:inline-block;">${val}</span>`;
      summaryDiv.appendChild(infoDiv);
    } catch (e) {
      // en cas d'erreur, on n'affiche rien de plus
    }
  }

  function renderExitStats(yearlyRows, monthlyRows) {
    if (!exitStatsContainer) return;

    const hasYear = yearlyRows && yearlyRows.length;
    const hasMonth = monthlyRows && monthlyRows.length;

    if (!hasYear && !hasMonth) {
      exitStatsContainer.textContent = "Aucune statistique de sortie disponible pour cet article.";
      if (exitStatsLinkWrapper) exitStatsLinkWrapper.innerHTML = "";
      return;
    }

    let html = "";

    // Conteneur flex pour afficher gauche/droite
    html += "<div style='display:flex; flex-wrap:wrap; gap:8px;'>";

    if (hasYear) {
      html += "<div style='flex:1 1 200px; min-width:0;'>";
      html += "<div style='margin-bottom:6px; font-weight:500;'>Statistiques de sorties par année</div>";
      html += "<table style='width:100%; border-collapse:collapse; margin-bottom:8px;'>";
      html += "<thead><tr>";
      html += "<th style='text-align:left; padding:2px 4px;'>Année</th>";
      html += "<th style='text-align:right; padding:2px 4px;'>Quantité sortie</th>";
      html += "</tr></thead><tbody>";

      yearlyRows.forEach(r => {
        const annee = r.annee != null ? String(r.annee) : "";
        const qte = r.qte_mvt != null ? String(r.qte_mvt) : "0";
        html += `<tr><td style="padding:2px 4px;">${annee}</td><td style="padding:2px 4px; text-align:right;">${qte}</td></tr>`;
      });

      html += "</tbody></table>";
      html += "</div>"; // fin colonne annuelle
    }

    if (hasMonth) {
      const currentYear = monthlyRows[0] && monthlyRows[0].annee != null
        ? String(monthlyRows[0].annee)
        : String(new Date().getFullYear());

      html += "<div style='flex:1 1 200px; min-width:0;'>";
      html += `<div style='margin:4px 0 2px; font-weight:500;'>Détail mensuel pour l'année ${currentYear}</div>`;
      html += "<table style='width:100%; border-collapse:collapse;'>";
      html += "<thead><tr>";
      html += "<th style='text-align:left; padding:2px 4px;'>Mois</th>";
      html += "<th style='text-align:right; padding:2px 4px;'>Quantité sortie</th>";
      html += "</tr></thead><tbody>";

      monthlyRows.forEach(r => {
        const mois = r.mois != null ? String(r.mois) : "";
        const qte = r.qte_mvt != null ? String(r.qte_mvt) : "0";
        html += `<tr><td style="padding:2px 4px;">${mois}</td><td style="padding:2px 4px; text-align:right;">${qte}</td></tr>`;
      });

      html += "</tbody></table>";
      html += "</div>"; // fin colonne mensuelle
    }

    html += "</div>"; // fin conteneur flex

    exitStatsContainer.innerHTML = html;

    if (exitStatsLinkWrapper) {
      const code = currentItemCode || "";
      if (code) {
        const url = `statistiques_sorties.html?code=${encodeURIComponent(code)}`;
        exitStatsLinkWrapper.innerHTML = `<a href="${url}" target="_blank" rel="noopener noreferrer">Ouvrir l'onglet dédié Statistiques sorties</a>`;
      } else {
        exitStatsLinkWrapper.innerHTML = "";
      }
    }
  }

  function renderHeliosSummary(data) {
    if (!heliosSummaryDiv) return;
    if (!data) {
      heliosSummaryDiv.textContent = "";
      if (heliosLinkWrapper) heliosLinkWrapper.innerHTML = "";
      return;
    }

    const code = data.code || "";
    const qty = data.quantity_active != null ? String(data.quantity_active) : "0";
    const sites = data.active_sites != null ? String(data.active_sites) : "0";

    let html = "<table style='width:100%; border-collapse:collapse;'>";
    html += `<tr><td style="padding:2px 4px; font-weight:500;">code_article</td><td style="padding:2px 4px;">${code}</td></tr>`;
    html += `<tr><td style="padding:2px 4px; font-weight:500;">quantite_active_parc</td><td style="padding:2px 4px;">${qty}</td></tr>`;
    html += `<tr><td style="padding:2px 4px; font-weight:500;">nb_sites_actifs</td><td style="padding:2px 4px;">${sites}</td></tr>`;
    html += "</table>";
    heliosSummaryDiv.innerHTML = html;

    if (heliosLinkWrapper) {
      const code = data.code || "";
      if (code) {
        const url = `helios.html?code=${encodeURIComponent(code)}`;
        heliosLinkWrapper.innerHTML = `<a href="${url}" target="_blank" rel="noopener noreferrer">Ouvrir le parc Helios détaillé pour cet article</a>`;
      } else {
        heliosLinkWrapper.innerHTML = "";
      }
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
      tr.addEventListener("click", async () => {
        const code = tr.dataset.codeArticle;
        currentItemCode = code || null;
        renderItemSummary(r);
        if (code) {
          loadStockForArticle(code);
          loadHeliosSummary(code);
          loadExitStats(code);
          loadCategorieSansSortie(code);
          updatePhotosLink(code);
        }
      });

      tbodyItems.appendChild(tr);

      // Si un code a été passé dans l'URL, sélectionner automatiquement la ligne correspondante
      if (currentItemCode && r.code_article && String(r.code_article).trim().toUpperCase() === currentItemCode.trim().toUpperCase()) {
        tr.click();
      }
    });
  }

  function renderStockTable(rows, codeArticle) {
    if (!theadStock || !tbodyStock) return;
    theadStock.innerHTML = "";
    tbodyStock.innerHTML = "";

    if (!rows.length) {
      if (stockSummaryLinkWrapper) stockSummaryLinkWrapper.innerHTML = "";
      return;
    }

    const first = rows[0] || {};
    let cols = Object.keys(first);

    const ordered = [];
    if (cols.includes("type_de_depot")) ordered.push("type_de_depot");
    if (cols.includes("flag_stock_d_m")) ordered.push("flag_stock_d_m");
    const remaining = cols.filter(c => !ordered.includes(c));
    cols = [...ordered, ...remaining];

    theadStock.innerHTML = cols.map(c => `<th style="text-align:left;">${c}</th>`).join("");

    rows.forEach(r => {
      const tr = document.createElement("tr");
      cols.forEach(c => {
        const td = document.createElement("td");
        td.textContent = r[c] != null ? String(r[c]) : "";
        tr.appendChild(td);
      });
      tbodyStock.appendChild(tr);
    });

    if (stockSummaryLinkWrapper) {
      const code = codeArticle || "";
      if (code) {
        const urlDetailed = `stock_detailed.html?code=${encodeURIComponent(code)}`;
        const urlHyper = `stock_hyper_detaille.html?code=${encodeURIComponent(code)}`;
        stockSummaryLinkWrapper.innerHTML = `
          <a href="${urlDetailed}" target="_blank" rel="noopener noreferrer">Voir le stock détaillé par magasin pour cet article</a><br>
          <a href="${urlHyper}" target="_blank" rel="noopener noreferrer">Ouvrir le stock hyper détaillé (par lot / série / projet)</a>
        `;
      } else {
        stockSummaryLinkWrapper.innerHTML = "";
      }
    }
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

  async function loadStockForArticle(code) {
    if (!code) return;
    if (theadStock) theadStock.innerHTML = "";
    if (tbodyStock) tbodyStock.innerHTML = "";

    try {
      const res = await fetch(API(`/auth/stock/${encodeURIComponent(code)}`));
      if (!res.ok) {
        renderStockTable([]);
        return;
      }
      const data = await res.json();
      const rows = data.rows || [];
      renderStockTable(rows, code);
    } catch (e) {
      renderStockTable([], code);
    }
  }

  async function loadHeliosSummary(code) {
    if (!code) {
      renderHeliosSummary(null);
      return;
    }
    try {
      const res = await fetch(API(`/helios/${encodeURIComponent(code)}`));
      if (!res.ok) {
        renderHeliosSummary(null);
        return;
      }
      const data = await res.json();
      renderHeliosSummary(data);
    } catch (e) {
      renderHeliosSummary(null);
    }
  }

  async function loadExitStats(code) {
    if (!exitStatsContainer) return;

    exitStatsContainer.textContent = "Chargement des statistiques de sorties...";

    if (!code) {
      exitStatsContainer.textContent = "";
      return;
    }

    try {
      const urlYear = new URL(API(`/items/${encodeURIComponent(code)}/stats-exit`));
      const urlMonth = new URL(API(`/items/${encodeURIComponent(code)}/stats-exit-monthly`));

      const paramsYear = urlYear.searchParams;
      const paramsMonth = urlMonth.searchParams;

      if (exitMotifCheckboxes && exitMotifCheckboxes.length) {
        exitMotifCheckboxes.forEach(cb => {
          if (cb.checked) {
            paramsYear.append("type_exit", cb.value);
            paramsMonth.append("type_exit", cb.value);
          }
        });
      }

      const [resYear, resMonth] = await Promise.all([
        fetch(urlYear.toString()),
        fetch(urlMonth.toString()),
      ]);

      if (!resYear.ok) {
        exitStatsContainer.textContent = `Erreur API statistiques de sorties annuelles (${resYear.status})`;
        return;
      }
      if (!resMonth.ok) {
        exitStatsContainer.textContent = `Erreur API statistiques de sorties mensuelles (${resMonth.status})`;
        return;
      }

      const dataYear = await resYear.json();
      const dataMonth = await resMonth.json();
      const rowsYear = dataYear.rows || [];
      const rowsMonth = dataMonth.rows || [];

      renderExitStats(rowsYear, rowsMonth);
    } catch (e) {
      exitStatsContainer.textContent = "Erreur de communication avec l'API statistiques de sorties";
    }
  }

  if (exitMotifCheckboxes && exitMotifCheckboxes.length) {
    exitMotifCheckboxes.forEach(cb => {
      cb.addEventListener("change", () => {
        if (currentItemCode) {
          loadExitStats(currentItemCode);
        }
      });
    });
  }

  if (form) {
    form.addEventListener("submit", (ev) => {
      ev.preventDefault();
      searchItems();
    });
  }
  if (btn) {
    btn.addEventListener("click", (ev) => {
      ev.preventDefault();
      searchItems();
    });
  }

  // Si un code article est passé dans l'URL (?code=...), lancer automatiquement la recherche
  try {
    const params = new URLSearchParams(window.location.search || "");
    const initialCode = (params.get("code") || "").trim();
    if (initialCode && qInput) {
      qInput.value = initialCode;
      currentItemCode = initialCode;
      searchItems();
    }
  } catch (e) {
    // en cas de problème avec l'URL, on n'applique pas de pré-remplissage
  }
});
