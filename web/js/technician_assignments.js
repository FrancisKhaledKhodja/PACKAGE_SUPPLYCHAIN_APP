document.addEventListener("DOMContentLoaded", () => {
  const qInput = document.getElementById("assign-q");
  const prInput = document.getElementById("assign-pr");
  const storeInput = document.getElementById("assign-store");
  const statusInput = document.getElementById("assign-status");
  const teamSelect = document.getElementById("assign-team");
  const rolesContainer = document.getElementById("assign-roles");
  const expandStoreRolesCb = document.getElementById("assign-expand-store-roles");
  const applyBtn = document.getElementById("assign-apply");
  const exportBtn = document.getElementById("assign-export");

  const tbody = document.getElementById("assign-tbody");
  const countDiv = document.getElementById("assign-count");

  let currentRows = [];

  // Pré-remplissage depuis l'URL (appelé par l'assistant)
  try {
    const params = new URLSearchParams(window.location.search || "");
    const q = (params.get("q") || "").trim();
    const pr = (params.get("pr") || "").trim();
    const store = (params.get("store") || "").trim();
    const status = (params.get("status") || "").trim();
    const expand = (params.get("expand_store_roles") || "").trim();
    const roles = params.getAll("roles").map(v => (v || "").trim()).filter(Boolean);

    if (q && qInput) qInput.value = q;
    if (pr && prInput) prInput.value = pr;
    if (store && storeInput) storeInput.value = store;
    if (status && statusInput) statusInput.value = status;
    if (expandStoreRolesCb && (expand === "1" || expand.toLowerCase() === "true" || expand.toLowerCase() === "yes")) {
      expandStoreRolesCb.checked = true;
    }

    if (rolesContainer && roles.length) {
      const cbs = Array.from(rolesContainer.querySelectorAll("input[type='checkbox'][name='assign-role']"));
      cbs.forEach(cb => {
        const val = String(cb.value || "").trim();
        if (val && roles.includes(val)) {
          cb.checked = true;
        }
      });
    }
  } catch (e) {
    // ignore erreur URL
  }

  function getSelectedRoles() {
    if (!rolesContainer) return [];
    const checked = Array.from(rolesContainer.querySelectorAll("input[type='checkbox'][name='assign-role']:checked"));
    return checked
      .map(cb => String(cb.value || "").trim())
      .filter(v => v);
  }

  function getFilteredRowsForDisplay(rows) {
    const selectedTeam = teamSelect?.value || "";
    const selectedRoles = getSelectedRoles();
    const expandStoreRoles = Boolean(expandStoreRolesCb && expandStoreRolesCb.checked);
    return rows
      .filter(r => {
        if (selectedTeam && (r.equipe || "") !== selectedTeam) return false;
        if (!expandStoreRoles) {
          if (selectedRoles.length) {
            const role = String(r.pr_role || "").trim();
            return selectedRoles.includes(role);
          }
        }
        return true;
      });
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
        "code_point_relais_store",
        "enseigne",
        "adresse_postale",
        "statut",
        "periode_absence_a_utiliser",
      ];
      cols.forEach(col => {
        const td = document.createElement("td");
        if (col === "code_point_relais_store") {
          td.classList.add("muted");
        }
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
    if (countDiv) {
      countDiv.textContent = "Chargement...";
    }
    const params = new URLSearchParams();
    const q = (qInput?.value || "").trim();
    const pr = (prInput?.value || "").trim();
    const store = (storeInput?.value || "").trim();
    const status = (statusInput?.value || "").trim();
    const roles = getSelectedRoles();
    const expandStoreRoles = Boolean(expandStoreRolesCb && expandStoreRolesCb.checked);

    if (q) params.set("q", q);
    if (pr) params.set("pr", pr);
    if (store) params.set("store", store);
    if (status) params.set("status", status);
    roles.forEach(r => params.append("roles", r));
    if (expandStoreRoles) params.set("expand_store_roles", "1");

    const url = API("/technicians/assignments") + (params.toString() ? "?" + params.toString() : "");
    try {
      const res = await fetch(url);
      if (!res.ok) {
        if (countDiv) {
          countDiv.textContent = `Erreur API (${res.status}) : impossible de charger les affectations.`;
        }
        if (tbody) tbody.innerHTML = "";
        return;
      }
      const data = await res.json().catch(() => null);
      if (!data || typeof data !== "object") {
        if (countDiv) {
          countDiv.textContent = "Erreur API : réponse JSON invalide.";
        }
        if (tbody) tbody.innerHTML = "";
        return;
      }
      const rows = data.rows || [];
      currentRows = rows;

      if (countDiv) {
        countDiv.textContent = rows.length ? `${rows.length} affectation(s)` : "Aucune affectation";
      }

      updateTeamOptions(rows);
      renderRows(rows);
    } catch (e) {
      if (countDiv) {
        countDiv.textContent = "API indisponible : démarrez l'API sur http://127.0.0.1:5001 (commande: py -m supplychain_app.run).";
      }
      if (tbody) tbody.innerHTML = "";
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
      "code_point_relais_store",
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

  if (rolesContainer) {
    rolesContainer.addEventListener("change", () => {
      renderRows(currentRows);
    });
  }

  if (expandStoreRolesCb) {
    expandStoreRolesCb.addEventListener("change", () => {
      loadAssignments();
    });
  }

  if (exportBtn) {
    exportBtn.addEventListener("click", () => {
      exportCsv();
    });
  }

  loadAssignments();
});
