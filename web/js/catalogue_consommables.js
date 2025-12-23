document.addEventListener("DOMContentLoaded", () => {
  const metaDiv = document.getElementById("conso-meta");
  const statusDiv = document.getElementById("conso-status");
  const grid = document.getElementById("conso-grid");
  const searchInput = document.getElementById("conso-search");
  const categorySelect = document.getElementById("conso-category");
  const refreshBtn = document.getElementById("conso-refresh");

  let allRows = [];
  let filtered = [];
  let columns = [];

  function toLc(v) {
    return (v == null ? "" : String(v)).toLowerCase();
  }

  function pick(row, keys) {
    for (const k of keys) {
      if (row && row[k] != null && String(row[k]).trim() !== "") return row[k];
    }
    return "";
  }

  function humanPrice(v) {
    if (v == null) return "";
    const s = String(v).trim();
    if (!s) return "";
    const n = Number(s.replace(",", "."));
    if (!isNaN(n)) {
      return n.toFixed(2) + " €";
    }
    return s;
  }

  function getCategorieSortieColor(value) {
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

  function buildCategories(rows) {
    const set = new Set();
    for (const r of rows || []) {
      const cat = String(pick(r, ["categorie", "category", "categorie_consommables", "famille", "famille_consommables"]) || "").trim();
      if (cat) set.add(cat);
    }
    return Array.from(set).sort((a, b) => a.localeCompare(b, "fr", { sensitivity: "base" }));
  }

  function render() {
    if (!grid) return;
    grid.innerHTML = "";

    if (!filtered.length) {
      const empty = document.createElement("div");
      empty.className = "conso-empty";
      empty.textContent = "Aucun article dans l'offre (ou aucun résultat avec ces filtres).";
      grid.appendChild(empty);
      return;
    }

    for (const row of filtered) {
      const code = String(pick(row, ["code_article", "code", "article", "sku"]) || "").trim();
      const lib = String(pick(row, ["libelle", "libelle_article", "designation", "nom", "libelle_court_article"]) || "").trim();
      const cat = String(pick(row, ["categorie", "category", "categorie_consommables", "famille", "famille_consommables"]) || "").trim();
      const sousCat = String(pick(row, ["sous_categorie", "sous_categorie_consommables", "sous_categorie_consommable", "sous_categorie"]) || "").trim();
      const price = humanPrice(pick(row, ["prix", "prix_eur", "prix_unitaire", "prix_previsionnel"]));
      const unit = String(pick(row, ["unite", "uom"]) || "").trim();
      const comment = String(pick(row, ["commentaire", "notes", "remarques"]) || "").trim();
      const stockMplc = pick(row, ["stock_mplc_good_m", "stock_mplc_good_mplc", "stock_mplc"]); 
      const sortiesConso = pick(row, ["sorties_conso_total", "sorties_conso_annee_en_cours", "sorties_conso"]);
      const categorieSortie = pick(row, ["categorie_sortie", "categorie_sans_sortie"]);

      const card = document.createElement("div");
      card.className = "conso-card";

      const h = document.createElement("h3");
      h.className = "conso-title";
      h.textContent = lib || code || "Article";

      const sub = document.createElement("p");
      sub.className = "conso-sub";
      sub.textContent = code ? `Code: ${code}` : "";

      const tags = document.createElement("div");
      tags.className = "conso-tags";
      const addTag = (txt) => {
        if (!txt) return;
        const t = document.createElement("span");
        t.className = "conso-tag";
        t.textContent = txt;
        tags.appendChild(t);
      };
      addTag(cat);
      addTag(sousCat);
      if (categorieSortie != null && String(categorieSortie).trim() !== "") {
        const val = String(categorieSortie);
        const t = document.createElement("span");
        t.className = "conso-tag";
        const color = getCategorieSortieColor(val);
        t.style.backgroundColor = color;
        t.style.color = "#000";
        t.textContent = val;
        tags.appendChild(t);
      }

      const details = document.createElement("div");
      details.className = "conso-details";

      const addRow = (k, v) => {
        if (!v) return;
        const r = document.createElement("div");
        r.className = "row";
        const kk = document.createElement("span");
        kk.className = "k";
        kk.textContent = k;
        const vv = document.createElement("span");
        vv.className = "v";
        vv.textContent = v;
        r.appendChild(kk);
        r.appendChild(vv);
        details.appendChild(r);
      };

      addRow("Prix", price);
      addRow("Unité", unit);
      if (stockMplc != null && String(stockMplc).trim() !== "") {
        const n = Number(String(stockMplc).replace(",", "."));
        const txt = !isNaN(n) ? n.toFixed(2) : String(stockMplc);
        addRow("Stock MPLC (good/M)", txt);
      }
      if (sortiesConso != null && String(sortiesConso).trim() !== "") {
        const n = Number(String(sortiesConso).replace(",", "."));
        const txt = !isNaN(n) ? n.toFixed(2) : String(sortiesConso);
        addRow("Sorties conso (total)", txt);
      }
      addRow("Commentaire", comment);


      const links = document.createElement("div");
      links.className = "conso-details";

      if (code) {
        const itemsUrl = `items.html?code=${encodeURIComponent(code)}`;
        const itemsLink = document.createElement("a");
        itemsLink.href = itemsUrl;
        itemsLink.target = "_blank";
        itemsLink.rel = "noopener noreferrer";
        itemsLink.textContent = "Voir la fiche article";
        links.appendChild(itemsLink);

        const photosLink = document.createElement("a");
        photosLink.href = `photos.html?code=${encodeURIComponent(code)}`;
        photosLink.target = "_blank";
        photosLink.rel = "noopener noreferrer";
        photosLink.textContent = "Voir les photos";
        photosLink.style.display = "none";
        links.appendChild(photosLink);

        fetch(API(`/auth/photos/local/${encodeURIComponent(code)}`), {
          method: "GET",
          credentials: "include",
        })
          .then((res) => (res.ok ? res.json() : null))
          .then((data) => {
            const files = data && Array.isArray(data.files) ? data.files : [];
            if (files.length) {
              photosLink.style.display = "inline";
            }
          })
          .catch(() => {
          });
      }

      card.appendChild(h);
      if (sub.textContent) card.appendChild(sub);
      if (tags.childNodes.length) card.appendChild(tags);
      if (details.childNodes.length) card.appendChild(details);
      if (links.childNodes.length) card.appendChild(links);

      grid.appendChild(card);
    }
  }

  function applyFilters() {
    const q = toLc(searchInput && searchInput.value ? searchInput.value.trim() : "");
    const catWanted = categorySelect && categorySelect.value ? String(categorySelect.value).trim() : "";

    filtered = (allRows || []).filter((r) => {
      if (catWanted) {
        const cat = String(pick(r, ["categorie", "category", "categorie_consommables", "famille", "famille_consommables"]) || "").trim();
        if (cat !== catWanted) return false;
      }
      if (q) {
        const hay = columns.map((c) => toLc(r[c])).join(" | ");
        if (!hay.includes(q)) return false;
      }
      return true;
    });

    filtered.sort((a, b) => {
      const libA = String(pick(a, ["libelle", "libelle_article", "designation", "nom", "libelle_court_article"]) || "").trim();
      const libB = String(pick(b, ["libelle", "libelle_article", "designation", "nom", "libelle_court_article"]) || "").trim();

      if (libA && libB) return libA.localeCompare(libB, "fr", { sensitivity: "base" });
      if (libA) return -1;
      if (libB) return 1;

      const codeA = String(pick(a, ["code_article", "code", "article", "sku"]) || "").trim();
      const codeB = String(pick(b, ["code_article", "code", "article", "sku"]) || "").trim();
      return codeA.localeCompare(codeB, "fr", { sensitivity: "base" });
    });

    if (statusDiv) {
      statusDiv.textContent = `${filtered.length} article(s) (sur ${allRows.length})`;
    }
    render();
  }

  function debounce(fn, delayMs) {
    let t = null;
    return (...args) => {
      if (t) clearTimeout(t);
      t = setTimeout(() => fn(...args), delayMs);
    };
  }

  const debouncedApply = debounce(applyFilters, 150);

  async function loadOffer() {
    if (statusDiv) statusDiv.textContent = "Chargement de l'offre...";
    if (grid) grid.innerHTML = "";
    try {
      const res = await fetch(API("/consommables/offer"), {
        method: "GET",
        credentials: "include",
      });
      const data = await res.json().catch(() => null);
      if (!data || !data.available) {
        const err = data && data.error ? String(data.error) : "offer_not_available";
        if (metaDiv) {
          metaDiv.textContent = "Offre indisponible (" + err + ")";
        }
        if (statusDiv) statusDiv.textContent = "";
        if (grid) {
          const empty = document.createElement("div");
          empty.className = "conso-empty";
          empty.textContent = "Aucune offre disponible pour le moment.";
          grid.appendChild(empty);
        }
        return;
      }

      allRows = Array.isArray(data.rows) ? data.rows : [];
      columns = Array.isArray(data.columns) ? data.columns : (allRows[0] ? Object.keys(allRows[0]) : []);

      const file = data.file || "";
      const ts = data.mtime_iso || "";
      if (metaDiv) {
        metaDiv.textContent = file ? `Source: ${file}${ts ? " (maj " + ts + ")" : ""}` : "";
      }

      const cats = buildCategories(allRows);
      if (categorySelect) {
        categorySelect.innerHTML = '<option value="">Toutes les catégories</option>'
          + cats.map((c) => `<option value="${String(c).replace(/"/g, "&quot;")}">${c}</option>`).join("\n");
      }

      applyFilters();
    } catch (e) {
      if (metaDiv) metaDiv.textContent = "Erreur lors du chargement de l'offre.";
      if (statusDiv) statusDiv.textContent = "";
    }
  }

  if (searchInput) searchInput.addEventListener("input", debouncedApply);
  if (categorySelect) categorySelect.addEventListener("change", applyFilters);
  if (refreshBtn) refreshBtn.addEventListener("click", loadOffer);

  loadOffer();
});
