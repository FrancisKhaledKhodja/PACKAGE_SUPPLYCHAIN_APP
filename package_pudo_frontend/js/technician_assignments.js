document.addEventListener("DOMContentLoaded", () => {
  const qInput = document.getElementById("assign-q");
  const prInput = document.getElementById("assign-pr");
  const storeInput = document.getElementById("assign-store");
  const statusInput = document.getElementById("assign-status");
  const teamSelect = document.getElementById("assign-team");
  const applyBtn = document.getElementById("assign-apply");
  const exportBtn = document.getElementById("assign-export");

  const tbody = document.getElementById("assign-tbody");
  const countDiv = document.getElementById("assign-count");

  let currentRows = [];

  function getFilteredRowsForDisplay(rows) {
    const selectedTeam = teamSelect?.value || "";
    return selectedTeam
      ? rows.filter(r => (r.equipe || "") === selectedTeam)
      : rows;
  }

  function renderRows(rows) {
    if (!tbody) return;
    tbody.innerHTML = "";
    const filtered = getFilteredRowsForDisplay(rows);

    filtered.forEach(r => {
      const tr = document.createElement("tr");
      const cols = [
        "code_magasin",
        "equipe",
        "technicien",
        "type_de_depot",
        "pr_role",
        "code_point_relais",
        "enseigne",
        "adresse_postale",
        "statut",
        "periode_absence_a_utiliser",
      ];
      cols.forEach(col => {
        const td = document.createElement("td");
        if (col === "statut") {
          const statut = r[col];
          if (statut != null && statut !== "") {
            const st = String(statut).toLowerCase();
            const isOpen = st.includes("ouvert") || ["1", "true", "actif", "active", "open"].includes(st);
            const isClosed = st.includes("ferme") || ["0", "false", "inactif", "inactive", "closed"].includes(st);
            const bg = isOpen ? "#16a34a" : (isClosed ? "#dc2626" : "#6b7280");
            const fg = "#ffffff";
            td.innerHTML = `<span style="display:inline-block; padding:2px 8px; border-radius:9999px; font-size:12px; font-weight:600; background:${bg}; color:${fg};">${statut}</span>`;
          } else {
            td.textContent = "";
          }
        } else {
          td.textContent = r[col] != null ? String(r[col]) : "";
        }
        tr.appendChild(td);
      });
      tbody.appendChild(tr);
    });
  }

  function updateTeamOptions(rows) {
    if (!teamSelect) return;
    const current = teamSelect.value || "";
    const teams = Array.from(new Set(
      rows
        .map(r => r.equipe)
        .filter(v => v != null && String(v).trim() !== "")
    )).sort();

    teamSelect.innerHTML = "";
    const optAll = document.createElement("option");
    optAll.value = "";
    optAll.textContent = "Toutes les équipes";
    teamSelect.appendChild(optAll);

    teams.forEach(t => {
      const opt = document.createElement("option");
      opt.value = String(t);
      opt.textContent = String(t);
      teamSelect.appendChild(opt);
    });

    // restore previous selection if possible
    if (current && teams.includes(current)) {
      teamSelect.value = current;
    }
  }

  async function loadAssignments() {
    const params = new URLSearchParams();
    const q = (qInput?.value || "").trim();
    const pr = (prInput?.value || "").trim();
    const store = (storeInput?.value || "").trim();
    const status = (statusInput?.value || "").trim();

    if (q) params.set("q", q);
    if (pr) params.set("pr", pr);
    if (store) params.set("store", store);
    if (status) params.set("status", status);

    const url = API("/technicians/assignments") + (params.toString() ? "?" + params.toString() : "");
    try {
      const res = await fetch(url);
      if (!res.ok) return;
      const data = await res.json();
      const rows = data.rows || [];
      currentRows = rows;

      if (countDiv) {
        countDiv.textContent = rows.length ? `${rows.length} affectation(s)` : "Aucune affectation";
      }

      updateTeamOptions(rows);
      renderRows(rows);
    } catch (e) {
      // ignore
    }
  }

  function exportCsv() {
    const rowsToExport = getFilteredRowsForDisplay(currentRows);

    if (!rowsToExport.length) {
      alert("Aucune donnée à exporter.");
      return;
    }
    const columns = [
      "code_magasin",
      "equipe",
      "technicien",
      "type_de_depot",
      "pr_role",
      "code_point_relais",
      "enseigne",
      "adresse_postale",
      "statut",
      "periode_absence_a_utiliser",
    ];
    const escapeCell = (val) => {
      if (val == null) return "";
      const s = String(val).replace(/"/g, '""');
      return '"' + s + '"';
    };
    const lines = [];
    lines.push(columns.map(escapeCell).join(";"));
    rowsToExport.forEach(r => {
      const line = columns.map(c => escapeCell(r[c])).join(";");
      lines.push(line);
    });
    const blob = new Blob([lines.join("\r\n")], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "technician_assignments.csv";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  if (applyBtn) {
    applyBtn.addEventListener("click", () => {
      loadAssignments();
    });
  }

  if (teamSelect) {
    teamSelect.addEventListener("change", () => {
      renderRows(currentRows);
    });
  }

  if (exportBtn) {
    exportBtn.addEventListener("click", () => {
      exportCsv();
    });
  }

  loadAssignments();
});
