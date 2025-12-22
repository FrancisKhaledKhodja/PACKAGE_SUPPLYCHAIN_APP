document.addEventListener("DOMContentLoaded", () => {
  const statusDiv = document.getElementById("pr-status");
  const countDiv = document.getElementById("pr-count");
  const theadRow = document.getElementById("pr-thead-row");
  const tbodyRows = document.getElementById("pr-tbody-rows");
  const searchInput = document.getElementById("pr-search");
  const enseigneInput = document.getElementById("pr-enseigne");
  const villeInput = document.getElementById("pr-ville");
  const cpInput = document.getElementById("pr-cp");
  const typeSelect = document.getElementById("pr-type");
  const btnRefresh = document.getElementById("btn-pr-refresh");
  const btnClear = document.getElementById("btn-pr-clear");
  const exportBtn = document.getElementById("export-pr-csv");

  let allRows = [];
  let filteredRows = [];
  let columns = [];

  function toLc(val) {
    return (val == null ? "" : String(val)).toLowerCase();
  }

  function classifyType(row) {
    const prest = toLc(row.nom_prestataire);
    const cat = toLc(row.categorie_pr_chronopost);
    const ens = toLc(row.enseigne);

    if (prest === "lm2s" || ens.includes("lm2s")) return "lm2s";
    if (prest === "tdf" || ens.includes("tdf")) return "tdf";
    if (cat.startsWith("c") || ens.includes("chronopost") || prest.includes("chrono")) return "chronopost";
    return "autre";
  }

  function computeColumns(rows) {
    if (!rows || !rows.length) return [];
    const preferred = [
      "code_point_relais",
      "enseigne",
      "adresse_1",
      "code_postal",
      "ville",
      "statut",
      "date_fermeture",
      "categorie_pr_chronopost",
      "nom_prestataire",
      "latitude",
      "longitude",
      "label",
    ];

    const keys = Object.keys(rows[0]);
    const cols = [];
    for (const p of preferred) {
      if (keys.includes(p)) cols.push(p);
    }
    for (const k of keys) {
      if (!cols.includes(k)) cols.push(k);
    }
    return cols;
  }

  function buildStatusBadge(statutRaw) {
    const txt = (statutRaw == null ? "" : String(statutRaw)).trim();
    const lower = txt.toLowerCase();
    const isOpen = lower.includes("ouvert") || lower === "open";
    const isClosed = lower.includes("fer") || lower === "closed";

    const span = document.createElement("span");
    span.textContent = txt || "";
    span.style.display = "inline-block";
    span.style.padding = "0.12rem 0.5rem";
    span.style.borderRadius = "999px";
    span.style.fontWeight = "600";
    span.style.fontSize = "0.8rem";

    if (isOpen) {
      span.style.backgroundColor = "#dcfce7";
      span.style.color = "#166534";
      span.style.border = "1px solid #86efac";
    } else if (isClosed) {
      span.style.backgroundColor = "#fee2e2";
      span.style.color = "#991b1b";
      span.style.border = "1px solid #fca5a5";
    } else {
      span.style.backgroundColor = "#e5e7eb";
      span.style.color = "#111827";
      span.style.border = "1px solid #d1d5db";
    }
    return span;
  }

  function getFermetureKeyFromColumns(cols) {
    if (!cols || !cols.length) return null;
    const found = cols.find((c) => String(c).toLowerCase().includes("fermet"));
    return found || null;
  }

  function renderTable(rows) {
    if (!theadRow || !tbodyRows) return;
    theadRow.innerHTML = "";
    tbodyRows.innerHTML = "";

    if (!rows || !rows.length) {
      if (countDiv) countDiv.textContent = "0 résultat";
      return;
    }

    for (const col of columns) {
      const th = document.createElement("th");
      th.textContent = col;
      theadRow.appendChild(th);
    }

    for (const row of rows) {
      const tr = document.createElement("tr");
      const fermetureKey = getFermetureKeyFromColumns(columns);
      for (const col of columns) {
        const td = document.createElement("td");
        const val = row[col];

        if (col === "statut") {
          td.appendChild(buildStatusBadge(val));
        } else {
          let txt = val != null ? String(val) : "";
          if (fermetureKey && col === fermetureKey && txt) {
            // affichage plus lisible si l'API renvoie un timestamp ou un ISO
            try {
              const d = new Date(txt);
              if (!isNaN(d.getTime())) {
                txt = d.toISOString().slice(0, 10);
              }
            } catch (e) {
            }
          }
          td.textContent = txt;
        }
        tr.appendChild(td);
      }
      tbodyRows.appendChild(tr);
    }

    if (countDiv) {
      const total = allRows.length;
      const shown = rows.length;
      countDiv.textContent = `${shown} résultat(s) (sur ${total})`;
    }
  }

  function applyFilters() {
    const q = toLc(searchInput && searchInput.value ? searchInput.value.trim() : "");
    const enseigne = toLc(enseigneInput && enseigneInput.value ? enseigneInput.value.trim() : "");
    const ville = toLc(villeInput && villeInput.value ? villeInput.value.trim() : "");
    const cp = (cpInput && cpInput.value ? String(cpInput.value).trim() : "");
    const type = typeSelect && typeSelect.value ? String(typeSelect.value) : "";

    filteredRows = (allRows || []).filter((row) => {
      if (enseigne && !toLc(row.enseigne).includes(enseigne)) return false;
      if (ville && !toLc(row.ville).includes(ville)) return false;
      if (cp) {
        const rowCp = row.code_postal == null ? "" : String(row.code_postal);
        if (!rowCp.startsWith(cp)) return false;
      }
      if (type) {
        const t = classifyType(row);
        if (t !== type) return false;
      }

      if (q) {
        const hay = columns.map((c) => toLc(row[c])).join(" | ");
        if (!hay.includes(q)) return false;
      }

      return true;
    });

    renderTable(filteredRows);
  }

  async function loadDirectory() {
    if (statusDiv) statusDiv.textContent = "Chargement de l'annuaire...";
    try {
      const res = await fetch(API("/pudo/directory"), {
        method: "GET",
        credentials: "include",
      });
      if (!res.ok) {
        if (statusDiv) statusDiv.textContent = "Impossible de charger l'annuaire (" + res.status + ").";
        return;
      }
      const data = await res.json();
      allRows = (data && data.rows) ? data.rows : [];
      columns = computeColumns(allRows);
      if (statusDiv) statusDiv.textContent = "";
      applyFilters();
    } catch (e) {
      if (statusDiv) statusDiv.textContent = "Erreur de communication avec l'API.";
    }
  }

  function exportCsvFromRows(rows, filename) {
    if (!rows || !rows.length) {
      alert("Aucune donnée à exporter.");
      return;
    }
    const cols = columns && columns.length ? columns : Object.keys(rows[0]);
    const escapeCell = (val) => {
      if (val == null) return "";
      const s = String(val).replace(/"/g, '""');
      return '"' + s + '"';
    };
    const lines = [];
    lines.push(cols.map(escapeCell).join(";"));
    for (const row of rows) {
      const line = cols.map((col) => escapeCell(row[col])).join(";");
      lines.push(line);
    }
    const blob = new Blob([lines.join("\r\n")], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  function debounce(fn, delayMs) {
    let t = null;
    return (...args) => {
      if (t) clearTimeout(t);
      t = setTimeout(() => fn(...args), delayMs);
    };
  }

  const debouncedApply = debounce(applyFilters, 150);

  if (searchInput) searchInput.addEventListener("input", debouncedApply);
  if (enseigneInput) enseigneInput.addEventListener("input", debouncedApply);
  if (villeInput) villeInput.addEventListener("input", debouncedApply);
  if (cpInput) cpInput.addEventListener("input", debouncedApply);
  if (typeSelect) typeSelect.addEventListener("change", applyFilters);

  if (btnRefresh) btnRefresh.addEventListener("click", loadDirectory);
  if (btnClear) {
    btnClear.addEventListener("click", () => {
      if (searchInput) searchInput.value = "";
      if (enseigneInput) enseigneInput.value = "";
      if (villeInput) villeInput.value = "";
      if (cpInput) cpInput.value = "";
      if (typeSelect) typeSelect.value = "";
      applyFilters();
    });
  }

  if (exportBtn) {
    exportBtn.addEventListener("click", () => {
      exportCsvFromRows(filteredRows, "annuaire_points_relais.csv");
    });
  }

  loadDirectory();
});
