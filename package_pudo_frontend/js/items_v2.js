document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("form-search");
  const qInput = document.getElementById("q");
  const theadRow = document.getElementById("thead-row");
  const tbodyRows = document.getElementById("tbody-rows");
  const resultsCount = document.getElementById("results-count");
  const detailsDiv = document.getElementById("details");

  function escapeHtml(str) {
    return (str == null ? "" : String(str))
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function renderKeyValueTable(obj) {
    const entries = Object.entries(obj || {});
    const rows = entries.map(([k, v]) => {
      const key = escapeHtml(k);
      let displayVal = v === null || v === undefined ? "" : String(v);
      let renderedVal = escapeHtml(displayVal);
      if (k === "criticite_pim") {
        const trimmed = displayVal.trim();
        let color = "#6b7280";
        if (trimmed === "0") color = "#22c55e";
        else if (trimmed === "1") color = "#eab308";
        else if (trimmed === "2") color = "#ef4444";
        const dot = `<span style="display:inline-block;width:10px;height:10px;border-radius:999px;background:${color};margin-right:6px;vertical-align:middle;"></span>`;
        renderedVal = dot + `<span>${escapeHtml(displayVal)}</span>`;
      }
      return `<tr><th style="text-align:left; padding:6px; border-bottom:1px solid rgba(255,255,255,0.06); width:30%; vertical-align:top;">${key}</th><td style="padding:6px; border-bottom:1px solid rgba(255,255,255,0.06);">${renderedVal}</td></tr>`;
    }).join("");
    return `<table style="width:100%; border-collapse:collapse;">${rows}</table>`;
  }

  function renderThemedDetails(item) {
    const src = item || {};
    const allFields = new Set(Object.keys(src || {}));

    function pickFields(fields) {
      const out = {};
      fields.forEach(name => {
        if (!Object.prototype.hasOwnProperty.call(src, name)) return;
        const v = src[name];
        if (v === null || v === undefined || String(v).trim() === "") return;
        out[name] = v;
        allFields.delete(name);
      });
      return out;
    }

    const blocks = [];

    const description = pickFields([
      "code_article",
      "libelle_court_article",
      "libelle_long_article",
      "commentaire_technique",
      "mnemonique",
      "role_responsable_et_equipement",
    ]);
    if (Object.keys(description).length) {
      blocks.push({ title: "Description article", data: description });
    }

    const statutTypeCriticite = pickFields([
      "statut_abrege_article",
      "cycle_de_vie_de_production_pim",
      "criticite_pim",
      "type_article",
      "suivi_par_num_serie_oui_non",
    ]);
    if (Object.keys(statutTypeCriticite).length) {
      blocks.push({ title: "Statut-Type-Criticite", data: statutTypeCriticite });
    }

    const feuilleCatalogue = pickFields([
      "feuille_du_catalogue",
      "description_de_la_feuille_du_catalogue",
    ]);
    if (Object.keys(feuilleCatalogue).length) {
      blocks.push({ title: "Feuille catalogue", data: feuilleCatalogue });
    }

    const achat = pickFields([
      "cycle_de_vie_achat",
      "compte_cg_achat",
      "description_famille_d_achat",
      "prix_EUR_catalogue_article",
      "prix_achat_prev",
    ]);
    if (Object.keys(achat).length) {
      blocks.push({ title: "Achat", data: achat });
    }

    const compta = pickFields([
      "categorie_immobilisation",
      "categorie_inv_accounting",
      "famille_immobilisation",
      "famille_d_achat_feuille_du_catalogue",
      "pump",
      "stocksecu_inv_oui_non",
    ]);
    if (Object.keys(compta).length) {
      blocks.push({ title: "Comptabilite", data: compta });
    }

    const poidsDim = pickFields([
      "article_hors_normes",
      "affretement",
      "fragile",
      "poids_article",
      "hauteur_article",
      "largeur_article",
      "longueur_article",
      "volume_article",
      "hors_gabarit_avion",
      "matiere_dangereuse",
      "md_classe",
      "md_code_classification",
      "md_code_onu",
      "md_etiquettes",
      "md_groupe_emballage",
      "md_qte_exceptee",
      "md_qte_limitee",
      "md_qte_reglementee",
      "md_type_colis",
      "nbre_colis",
      "conditionnement",
    ]);
    if (Object.keys(poidsDim).length) {
      blocks.push({ title: "Poids - Dimension - Contrainte Transport", data: poidsDim });
    }

    const appro = pickFields([
      "delai_approvisionnement",
      "qte_cde_maximum_quantite_d_ordre_de_commande",
      "qte_cde_minimum_point_de_reappro",
      "qte_max_de_l_article",
      "qte_maximum_ordre_de_commande",
      "qte_min_de_l_article",
      "qte_minimum_ordre_de_commande",
      "quantite_a_commander",
      "point_de_commande",
    ]);
    if (Object.keys(appro).length) {
      blocks.push({ title: "Approvisionnement", data: appro });
    }

    const logistique = pickFields([
      "retour_production",
      "catalogue_consommable",
      "article_de_consommable",
      "commentaire_logistique",
      "consigne_prestataire",
      "dtom",
      "duree_de_garantie_neuf",
      "duree_de_garantie_sav",
      "peremption",
      "type_transport",
    ]);
    if (Object.keys(logistique).length) {
      blocks.push({ title: "Logistique", data: logistique });
    }

    const reparation = pickFields([
      "delai_de_reparation_contractuel",
      "description_lieu_de_reparation",
      "lieu_de_reparation_pim",
      "a_retrofiter",
      "rma",
    ]);
    if (Object.keys(reparation).length) {
      blocks.push({ title: "Réparation", data: reparation });
    }

    const creation = pickFields([
      "date_creation_article",
      "date_derniere_modif_article",
      "nom_createur_article",
      "auteur_derniere_modif_article",
    ]);
    if (Object.keys(creation).length) {
      blocks.push({ title: "Création article", data: creation });
    }

    if (!blocks.length) return "";

    const inner = blocks.map(block => {
      return `
        <div style="break-inside:avoid; -webkit-column-break-inside:avoid; margin-bottom:8px;">
          <div style="font-weight:600; margin-bottom:6px; font-size:1rem;">${escapeHtml(block.title)}</div>
          <div class="card">
            <div style="overflow:auto; max-height:40vh;">
              ${renderKeyValueTable(block.data)}
            </div>
          </div>
        </div>`;
    }).join("");

    return `
      <div class="section"></div>
      <div style="column-count:2; column-gap:12px; -webkit-column-count:2; -webkit-column-gap:12px;">
        ${inner}
      </div>`;
  }

  function getCategorieSansSortieColor(value) {
    const v = (value || "").trim();
    switch (v) {
      case "1 - moins de 2 mois":
        return "#33CC00";
      case "2 - entre 2 et 6 mois":
        return "#66AA00";
      case "3 - entre 6 mois et 1 an ":
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

  function renderArrayOfObjects(arr, title) {
    const items = Array.isArray(arr) ? arr : [];
    if (!items.length) return "";
    const cols = Array.from(items.reduce((s, o) => { Object.keys(o || {}).forEach(k => s.add(k)); return s; }, new Set()));
    const thead = `<thead><tr>${cols.map(c => `<th style="text-align:left; padding:6px; border-bottom:1px solid rgba(255,255,255,0.06);">${escapeHtml(c)}</th>`).join('')}</tr></thead>`;
    const tbody = `<tbody>${items.map(o => `<tr>${cols.map(c => `<td style="padding:6px; border-bottom:1px solid rgba(255,255,255,0.06);">${escapeHtml(o[c] == null ? '' : String(o[c]))}</td>`).join('')}</tr>`).join('')}</tbody>`;
    return `
      <div class="section"></div>
      <div style="font-weight:600; margin-bottom:6px;">${escapeHtml(title)}</div>
      <div class="card">
        <div style="overflow:auto; max-height:40vh;">
          <table style="width:100%; border-collapse:collapse;">${thead}${tbody}</table>
        </div>
      </div>`;
  }

  function renderArrayOfObjectsOrEmpty(arr, title, emptyMessage) {
    const items = Array.isArray(arr) ? arr : [];
    if (!items.length) {
      return `
        <div class="section"></div>
        <div style="font-weight:600; margin-bottom:6px;">${escapeHtml(title)}</div>
        <div class="card">
          <div class="muted" style="padding:8px 12px;">${escapeHtml(emptyMessage)}</div>
        </div>`;
    }
    return renderArrayOfObjects(items, title);
  }

  function renderDetailsPayload(payload, fallbackItem) {
    const apiItem = payload && payload.item ? payload.item : {};
    const baseItem = (apiItem && Object.keys(apiItem).length) ? apiItem : (fallbackItem || {});
    const manufacturers = payload && payload.manufacturers ? payload.manufacturers : [];
    const equivalentsRaw = payload && payload.equivalents ? payload.equivalents : [];
    let html = "";
    html += renderThemedDetails(baseItem);
    const manufacturersSlim = manufacturers.map(row => {
      const r = row || {};
      const { code_article, libelle_court_article, ...rest } = r;
      return rest;
    });
    html += renderArrayOfObjectsOrEmpty(
      manufacturersSlim,
      "Références fournisseurs",
      "Aucune référence fournisseur trouvée pour cet article."
    );

    // Pour les équivalences, on masque certaines colonnes techniques
    const equivalents = equivalentsRaw.map(row => {
      const r = { ...(row || {}) };
      delete r["__matched_by"];
      delete r["libelle_court_article"];
      return r;
    });
    html += renderArrayOfObjectsOrEmpty(
      equivalents,
      "Équivalences",
      "Aucun article équivalent trouvé pour cet article."
    );
    return html;
  }

  function renderNomenclature(ascii) {
    const txt = ascii ? String(ascii) : "";
    if (!txt.trim()) return "";
    return `
      <div class="section"></div>
      <h2>Nomenclature</h2>
      <div class="card" style="margin-top:4px;">
        <pre style="margin:0; padding:12px; overflow:auto; max-height:40vh; white-space:pre;">${escapeHtml(txt)}</pre>
      </div>`;
  }

  async function searchItems() {
    const q = (qInput && qInput.value || "").trim();
    if (resultsCount) resultsCount.textContent = "";
    if (theadRow) theadRow.innerHTML = "";
    if (tbodyRows) tbodyRows.innerHTML = "";
    if (detailsDiv) detailsDiv.innerHTML = "";
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
      if (resultsCount) resultsCount.textContent = rows.length ? `${rows.length} résultat(s)` : "Aucun résultat";
      if (theadRow) {
        theadRow.innerHTML = cols.map(c => `<th>${escapeHtml(c)}</th>`).join("");
      }
      if (tbodyRows) {
        tbodyRows.innerHTML = "";
        rows.forEach(r => {
          const tr = document.createElement("tr");
          tr.className = "item-row";
          // on conserve toutes les colonnes dans data-full pour le détail
          tr.dataset.full = JSON.stringify(r);
          cols.forEach(c => {
            const td = document.createElement("td");
            td.textContent = r[c] != null ? String(r[c]) : "";
            if (c === "code_article" || c === "libelle_court_article") {
              td.style.fontSize = "0.8rem";
            }
            tr.appendChild(td);
          });
          tbodyRows.appendChild(tr);
        });
      }
    } catch (e) {
      if (resultsCount) resultsCount.textContent = "Erreur de recherche";
    }
  }

  async function loadDetailsForRow(tr) {
    if (!tr) return;
    const rowsNode = tbodyRows;
    if (rowsNode) {
      rowsNode.querySelectorAll("tr").forEach(row => row.style.background = "");
      tr.style.background = "rgba(255,255,255,0.06)";
    }
    let full = {};
    try { full = JSON.parse(tr.dataset.full || "{}"); } catch (e) { full = {}; }

    // essayer d'identifier le code article
    let code = (full.code_article || full.code || full.id_article || "").toString();
    if (!code && theadRow) {
      const headers = Array.from(theadRow.querySelectorAll("th")).map(th => (th.textContent || "").trim());
      const values = Array.from(tr.querySelectorAll("td")).map(td => (td.textContent || "").trim());
      let idx = -1;
      for (let i = 0; i < headers.length; i++) {
        const h = headers[i].toLowerCase();
        if (h === "code_article" || /code.*article/.test(h)) { idx = i; break; }
        if (h === "code" || h === "id_article") { idx = i; break; }
      }
      if (idx >= 0 && values[idx]) {
        code = values[idx].toString();
      }
    }
    if (!code) {
      if (detailsDiv) {
        detailsDiv.innerHTML = renderKeyValueTable(full);
      }
      return;
    }

    try {
      const [detailRes, bomRes, catRes] = await Promise.all([
        fetch(API(`/items/${encodeURIComponent(code)}/details`)),
        fetch(API(`/items/${encodeURIComponent(code)}/nomenclature`)),
        fetch(API(`/items/${encodeURIComponent(code)}/categorie-sans-sortie`)),
      ]);

      let html = "";
      let baseItem = full;

      if (detailRes.ok) {
        const payload = await detailRes.json();
        html += renderDetailsPayload(payload, baseItem);
      } else {
        const fallbackPayload = { item: baseItem };
        html += renderDetailsPayload(fallbackPayload, baseItem);
      }

      if (bomRes.ok) {
        const bom = await bomRes.json();
        html += renderNomenclature(bom.ascii || "");
      }

      if (catRes && catRes.ok) {
        const cat = await catRes.json();
        const val = cat && cat.categorie_sans_sortie != null ? String(cat.categorie_sans_sortie) : "";
        if (val) {
          const color = getCategorieSansSortieColor(val);
          html += `
            <div class="section"></div>
            <div class="card">
              <div style="padding:8px 12px;">
                <div style="font-weight:600; margin-bottom:4px;">Catégorie sans sortie</div>
                <div><span style="background-color:${color}; color:#000; padding:2px 6px; border-radius:4px; display:inline-block;">${escapeHtml(val)}</span></div>
              </div>
            </div>`;
        }
      }

      if (detailsDiv) {
        detailsDiv.innerHTML = html;
      }
    } catch (e) {
      if (detailsDiv) {
        let themed = renderThemedDetails(full);
        if (!themed || !themed.trim()) {
          themed = renderKeyValueTable(full);
        }
        detailsDiv.innerHTML = themed;
      }
    }
  }

  async function loadDetailsByCode(codeParam) {
    const code = (codeParam || "").toString().trim();
    if (!code) return;
    if (detailsDiv) {
      detailsDiv.innerHTML = "Chargement des détails de l'article...";
    }

    try {
      const [detailRes, bomRes, catRes] = await Promise.all([
        fetch(API(`/items/${encodeURIComponent(code)}/details`)),
        fetch(API(`/items/${encodeURIComponent(code)}/nomenclature`)),
        fetch(API(`/items/${encodeURIComponent(code)}/categorie-sans-sortie`)),
      ]);

      let html = "";
      const baseItem = { code_article: code };

      if (detailRes.ok) {
        const payload = await detailRes.json();
        html += renderDetailsPayload(payload, baseItem);
      } else {
        const fallbackPayload = { item: baseItem };
        html += renderDetailsPayload(fallbackPayload, baseItem);
      }

      if (bomRes.ok) {
        const bom = await bomRes.json();
        html += renderNomenclature(bom.ascii || "");
      }

      if (catRes && catRes.ok) {
        const cat = await catRes.json();
        const val = cat && cat.categorie_sans_sortie != null ? String(cat.categorie_sans_sortie) : "";
        if (val) {
          html += `
            <div class="section"></div>
            <div class="card">
              <div style="padding:8px 12px;">
                <div style="font-weight:600; margin-bottom:4px;">Catégorie sans sortie</div>
                <div>${escapeHtml(val)}</div>
              </div>
            </div>`;
        }
      }

      if (detailsDiv) {
        detailsDiv.innerHTML = html;
      }
    } catch (e) {
      if (detailsDiv) {
        detailsDiv.innerHTML = `<div class="card"><div class="muted" style="padding:8px 12px;">Impossible de charger les détails pour le code ${code}.</div></div>`;
      }
    }
  }

  if (form) {
    form.addEventListener("submit", (ev) => {
      ev.preventDefault();
      searchItems();
    });
  }

  if (tbodyRows) {
    tbodyRows.addEventListener("click", (ev) => {
      let tr = ev.target;
      while (tr && tr.tagName !== "TR") tr = tr.parentElement;
      if (!tr || !tr.classList.contains("item-row")) return;
      loadDetailsForRow(tr);
    });
  }

  // Initialisation avec paramètre ?code=... pour ouvrir directement un article
  (async () => {
    try {
      const url = new URL(window.location.href);
      const codeParam = (url.searchParams.get("code") || "").trim();
      if (!codeParam) return;

      if (qInput) qInput.value = codeParam;
      await searchItems();
      await loadDetailsByCode(codeParam);
    } catch (e) {
      // ignore erreur d'URL
    }
  })();
});
