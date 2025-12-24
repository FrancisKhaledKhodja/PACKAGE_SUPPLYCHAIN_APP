const ADMIN_PR_PASSWORD = "adminPR2025";

function initAdminPRPage() {
  document.addEventListener("DOMContentLoaded", () => {
    const loginBox = document.getElementById("admin-pr-login");
    const content = document.getElementById("admin-pr-content");
    const pwdInput = document.getElementById("admin-pr-password");
    const loginBtn = document.getElementById("admin-pr-login-btn");
    const msg = document.getElementById("admin-pr-login-msg");

    if (!loginBox || !content || !pwdInput || !loginBtn) {
      // si pour une raison quelconque le bloc n'existe pas,
      // on lance quand même la logique
      initAdminPRLogic();
      return;
    }

    const tryUnlock = () => {
      const val = (pwdInput.value || "").trim();
      if (val === ADMIN_PR_PASSWORD) {
        loginBox.style.display = "none";
        content.style.display = "";
        initAdminPRLogic();
      } else {
        if (msg) msg.textContent = "Mot de passe incorrect.";
      }
    };

    loginBtn.addEventListener("click", tryUnlock);
    pwdInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        tryUnlock();
      }
    });
  });
}


function initAdminPRLogic() {
  const searchInput = document.getElementById("tech-search");
  const typesContainer = document.getElementById("tech-types");
  const applyBtn = document.getElementById("btn-tech-apply");
  const contactsSelect = document.getElementById("tech-contacts");
  const showBtn = document.getElementById("btn-tech-show");

  const emptyMsg = document.getElementById("tech-details-empty");
  const detailsContent = document.getElementById("tech-details-content");
  const codeMagasin = document.getElementById("tech-code-magasin");
  const libelleMagasin = document.getElementById("tech-libelle-magasin");
  const equipe = document.getElementById("tech-equipe");
  const responsable = document.getElementById("tech-responsable");
  const contact = document.getElementById("tech-contact");
  const telephone = document.getElementById("tech-telephone");
  const email = document.getElementById("tech-email");
  const adresse = document.getElementById("tech-adresse");
  const codeIg = document.getElementById("tech-code-ig");
  const adresseIg = document.getElementById("tech-adresse-ig");
  const libelleLongIg = document.getElementById("tech-libelle-long-ig");

  const prPrincipalCode = document.getElementById("pr-principal-code");
  const prPrincipalCodeStore = document.getElementById("pr-principal-code-store");
  const prPrincipalEns = document.getElementById("pr-principal-enseigne");
  const prPrincipalAdr = document.getElementById("pr-principal-adresse");
  const prPrincipalMeta = document.getElementById("pr-principal-meta");
  const prPrincipalStatut = document.getElementById("pr-principal-statut");
  const prPrincipalDrive = document.getElementById("pr-principal-drive");

  const prBackupCode = document.getElementById("pr-backup-code");
  const prBackupCodeStore = document.getElementById("pr-backup-code-store");
  const prBackupEns = document.getElementById("pr-backup-enseigne");
  const prBackupAdr = document.getElementById("pr-backup-adresse");
  const prBackupMeta = document.getElementById("pr-backup-meta");
  const prBackupStatut = document.getElementById("pr-backup-statut");
  const prBackupDrive = document.getElementById("pr-backup-drive");

  const prHnCode = document.getElementById("pr-hn-code");
  const prHnCodeStore = document.getElementById("pr-hn-code-store");
  const prHnEns = document.getElementById("pr-hn-enseigne");
  const prHnAdr = document.getElementById("pr-hn-adresse");
  const prHnMeta = document.getElementById("pr-hn-meta");
  const prHnStatut = document.getElementById("pr-hn-statut");
  const prHnDrive = document.getElementById("pr-hn-drive");

  const prPrincipalSelect = document.getElementById("pr-principal-admin-select");
  const prPrincipalComment = document.getElementById("pr-principal-admin-comment");
  const prPrincipalInfo = document.getElementById("pr-principal-admin-info");

  const prBackupSelect = document.getElementById("pr-backup-admin-select");
  const prBackupComment = document.getElementById("pr-backup-admin-comment");
  const prBackupInfo = document.getElementById("pr-backup-admin-info");

  const prHnSelect = document.getElementById("pr-hn-admin-select");
  const prHnComment = document.getElementById("pr-hn-admin-comment");
  const prHnInfo = document.getElementById("pr-hn-admin-info");

  const saveBtn = document.getElementById("btn-pr-admin-save");

  let currentTypes = [];
  let pudoDirectory = [];

  console.log("INIT ADMIN PR LOGIC OK");
  console.log("showBtn =", showBtn);

  if (showBtn) {
    showBtn.addEventListener("click", () => {
      console.log("CLICK AFFICHER, valeur =", contactsSelect.value);
      loadDetails();
    });
  }

  function renderPr(prData, codeEl, codeStoreEl, ensEl, adrEl, metaEl, statutEl, driveEl, distanceByPr) {
    if (!codeEl || !prData) {
      if (codeEl) codeEl.textContent = "";
      if (codeStoreEl) codeStoreEl.textContent = "";
      if (ensEl) ensEl.textContent = "";
      if (adrEl) adrEl.textContent = "";
      if (metaEl) metaEl.textContent = "";
      if (statutEl) statutEl.textContent = "";
      if (driveEl) driveEl.textContent = "";
      return;
    }
    const code = prData.code_point_relais || "";
    const codeStore = prData.code_point_relais_store || "";
    const displayCode = code || codeStore;
    const enseigne = prData.enseigne || "";
    const adr = prData.adresse_postale || "";
    const categoriePr = prData.categorie || "";
    const prestataire = prData.prestataire || "";
    const statut = prData.statut || "";

    codeEl.textContent = displayCode;
    if (codeStoreEl) {
      codeStoreEl.textContent = codeStore ? `Code PR (SPEED): ${codeStore}` : "";
    }
    if (ensEl) ensEl.textContent = enseigne;
    if (adrEl) adrEl.textContent = adr;
    if (metaEl) {
      if (categoriePr || prestataire) {
        const parts = [];
        if (categoriePr) parts.push(`Catégorie: ${categoriePr}`);
        if (prestataire) parts.push(`Prestataire: ${prestataire}`);
        metaEl.textContent = parts.join(" • ");
      } else {
        metaEl.textContent = "";
      }
    }

    if (statutEl) {
      const st = String(statut || "").toLowerCase();
      const isOpen = st.includes("ouvert") || ["1", "true", "actif", "active", "open"].includes(st);
      const isClosed = st.includes("ferme") || ["0", "false", "inactif", "inactive", "closed"].includes(st);
      const css = isOpen ? "status-badge--open" : (isClosed ? "status-badge--closed" : "status-badge--unknown");
      statutEl.innerHTML = statut
        ? `<span class="status-badge ${css}">Statut: ${statut}</span>`
        : "";
    }

    if (driveEl) {
      const map = distanceByPr || {};
      const row = map[displayCode] || map[codeStore] || null;
      if (!row) {
        driveEl.textContent = "Distance/durée indisponibles";
      } else {
        const parts = [];

        const distM = row.distance;
        const distMNum = distM === null || distM === undefined || String(distM) === "" ? null : Number(distM);
        if (distMNum !== null && Number.isFinite(distMNum)) {
          const km = distMNum / 1000;
          parts.push(`Distance: ${km.toFixed(1)} km`);
        }

        const durS = row.duration;
        const durSNum = durS === null || durS === undefined || String(durS) === "" ? null : Number(durS);
        if (durSNum !== null && Number.isFinite(durSNum)) {
          const mins = Math.round(durSNum / 60);
          parts.push(`Durée: ${mins} min`);
        }

        driveEl.textContent = parts.length ? parts.join(" • ") : "Distance/durée indisponibles";
      }
    }
  }

  async function loadContacts() {
    const q = (searchInput?.value || "").trim();
    const params = new URLSearchParams();
    if (q) params.set("q", q);
    currentTypes.forEach(t => params.append("types", t));

    const url = API("/technicians/contacts") + (params.toString() ? "?" + params.toString() : "");
    try {
      const res = await fetch(url);
      if (!res.ok) return;
      const data = await res.json();
      const contacts = data.contacts || [];
      const storeTypes = data.store_types || [];

      typesContainer.innerHTML = "";
      storeTypes.forEach(t => {
        const label = document.createElement("label");
        const cb = document.createElement("input");
        cb.type = "checkbox";
        cb.value = t;
        cb.name = "types";
        if (currentTypes.includes(t)) {
          cb.checked = true;
        }
        label.appendChild(cb);
        label.appendChild(document.createTextNode(" " + t));
        typesContainer.appendChild(label);
      });

      contactsSelect.innerHTML = "";
      contacts.forEach(c => {
        const opt = document.createElement("option");
        opt.value = c.value;
        opt.textContent = c.label;
        contactsSelect.appendChild(opt);
      });
    } catch (e) {
      // ignore
    }
  }

  async function loadOverrides(code) {
    if (!code) return;
    try {
      const res = await fetch(API(`/technicians/${encodeURIComponent(code)}/pr_overrides`));
      if (!res.ok) return;
      const data = await res.json() || {};
      const roles = {
        principal: { sel: prPrincipalSelect, comment: prPrincipalComment, info: prPrincipalInfo },
        backup: { sel: prBackupSelect, comment: prBackupComment, info: prBackupInfo },
        hors_normes: { sel: prHnSelect, comment: prHnComment, info: prHnInfo },
      };
      Object.keys(roles).forEach(role => {
        const r = roles[role];
        const v = data[role] || null;
        if (!r.sel || !r.comment || !r.info) return;
        r.sel.value = v && v.code ? String(v.code) : "";
        r.comment.value = v && v.commentaire ? String(v.commentaire) : "";
        const dateTxt = v && v.date_commentaire ? `Dernier commentaire le ${v.date_commentaire}` : "";
        r.info.textContent = dateTxt;
      });
    } catch (e) {
      // ignore
    }
  }

  async function loadDetails() {
    const code = contactsSelect.value;
    if (!code) {
    console.log("loadDetails: pas de code magasin");
    return;
  }
  
  const url = API(`/technicians/${encodeURIComponent(code)}`);
  console.log("loadDetails: appel API", url);

    try {
      const res = await fetch(API(`/technicians/${encodeURIComponent(code)}`));
      if (!res.ok) return;
      const data = await res.json();
      const d = data.details || {};
      const pr = data.pr_details || {};

      const distanceByPr = {};
      try {
        const resDist = await fetch(API(`/technicians/${encodeURIComponent(code)}/distances_pr`));
        if (resDist.ok) {
          const distData = await resDist.json();
          const rows = distData && distData.rows ? distData.rows : [];
          rows.forEach(r => {
            if (!r) return;
            const prKey = (r.code_point_relais || r.code_pr || r.pr || "").toString().trim();
            if (!prKey) return;
            distanceByPr[prKey] = r;
          });
        }
      } catch (e) {
        // ignore
      }

      codeMagasin.textContent = d.code_magasin || "";
      libelleMagasin.textContent = d.libelle_magasin || "";
      equipe.textContent = d.equipe || "";
      responsable.textContent = d.responsable || "";
      contact.textContent = d.contact || "";
      telephone.textContent = d.telephone || "";
      email.textContent = d.email || "";
      adresse.textContent = d.adresse || "";
      codeIg.textContent = d.code_ig || "";
      if (libelleLongIg) libelleLongIg.textContent = d.libelle_long_ig || "";
      adresseIg.textContent = d.adresse_ig || "";

      renderPr(pr.principal, prPrincipalCode, prPrincipalCodeStore, prPrincipalEns, prPrincipalAdr, prPrincipalMeta, prPrincipalStatut, prPrincipalDrive, distanceByPr);
      renderPr(pr.backup, prBackupCode, prBackupCodeStore, prBackupEns, prBackupAdr, prBackupMeta, prBackupStatut, prBackupDrive, distanceByPr);
      renderPr(pr.hors_normes, prHnCode, prHnCodeStore, prHnEns, prHnAdr, prHnMeta, prHnStatut, prHnDrive, distanceByPr);

      await loadOverrides(code);

      if (emptyMsg) emptyMsg.style.display = "none";
      if (detailsContent) detailsContent.style.display = "block";
    } catch (e) {
      // ignore
    }
  }

  async function saveOverrides() {
    const code = contactsSelect.value;
    if (!code) return;
    const payload = {
      principal: {
        code: prPrincipalSelect ? prPrincipalSelect.value : "",
        commentaire: prPrincipalComment ? prPrincipalComment.value : "",
      },
      backup: {
        code: prBackupSelect ? prBackupSelect.value : "",
        commentaire: prBackupComment ? prBackupComment.value : "",
      },
      hors_normes: {
        code: prHnSelect ? prHnSelect.value : "",
        commentaire: prHnComment ? prHnComment.value : "",
      },
    };
    try {
      const res = await fetch(API(`/technicians/${encodeURIComponent(code)}/pr_overrides`), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        alert("Erreur lors de la sauvegarde des choix PR.");
        return;
      }
      const data = await res.json();
      const roles = {
        principal: { info: prPrincipalInfo },
        backup: { info: prBackupInfo },
        hors_normes: { info: prHnInfo },
      };
      Object.keys(roles).forEach(role => {
        const v = data[role] || null;
        const infoEl = roles[role].info;
        if (!infoEl) return;
        const dateTxt = v && v.date_commentaire ? `Dernier commentaire le ${v.date_commentaire}` : "";
        infoEl.textContent = dateTxt;
      });
      alert("Choix PR administrateur sauvegardés.");
    } catch (e) {
      alert("Erreur lors de la sauvegarde des choix PR.");
    }
  }

  if (applyBtn) {
    applyBtn.addEventListener("click", () => {
      const checked = Array.from(typesContainer.querySelectorAll("input[type='checkbox']:checked"));
      currentTypes = checked.map(cb => cb.value);
      loadContacts();
    });
  }

  if (showBtn) {
    showBtn.addEventListener("click", () => {
      loadDetails();
    });
  }

  if (saveBtn) {
    saveBtn.addEventListener("click", () => {
      saveOverrides();
    });
  }

  loadPudoDirectory();
  loadContacts();
};

initAdminPRPage();
