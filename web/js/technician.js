document.addEventListener("DOMContentLoaded", () => {
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
  const prPrincipalEns = document.getElementById("pr-principal-enseigne");
  const prPrincipalAdr = document.getElementById("pr-principal-adresse");
  const prPrincipalMeta = document.getElementById("pr-principal-meta");
  const prPrincipalStatut = document.getElementById("pr-principal-statut");
  const prPrincipalCodeStore = document.getElementById("pr-principal-code-store");

  const prBackupCode = document.getElementById("pr-backup-code");
  const prBackupEns = document.getElementById("pr-backup-enseigne");
  const prBackupAdr = document.getElementById("pr-backup-adresse");
  const prBackupMeta = document.getElementById("pr-backup-meta");
  const prBackupStatut = document.getElementById("pr-backup-statut");
  const prBackupCodeStore = document.getElementById("pr-backup-code-store");

  const prHnCode = document.getElementById("pr-hn-code");
  const prHnEns = document.getElementById("pr-hn-enseigne");
  const prHnAdr = document.getElementById("pr-hn-adresse");
  const prHnMeta = document.getElementById("pr-hn-meta");
  const prHnStatut = document.getElementById("pr-hn-statut");
  const prHnCodeStore = document.getElementById("pr-hn-code-store");

  let currentTypes = [];

  // Pré-remplissage depuis l'URL (appelé par l'assistant)
  let initialQuery = "";
  try {
    const params = new URLSearchParams(window.location.search || "");
    initialQuery = (params.get("q") || "").trim();
    if (initialQuery && searchInput) {
      searchInput.value = initialQuery;
    }
  } catch (e) {
    initialQuery = "";
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

      // Render types
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

      // Render contacts
      contactsSelect.innerHTML = "";
      contacts.forEach(c => {
        const opt = document.createElement("option");
        opt.value = c.value;
        opt.textContent = c.label;
        contactsSelect.appendChild(opt);
      });

      // Si une recherche initiale est fournie via ?q=..., sélectionner automatiquement la meilleure correspondance
      if (initialQuery) {
        const needle = initialQuery.toLowerCase();
        let best = null;
        for (let i = 0; i < contactsSelect.options.length; i += 1) {
          const opt = contactsSelect.options[i];
          const v = (opt.value || "").toString().toLowerCase();
          const lbl = (opt.textContent || "").toString().toLowerCase();
          if (v === needle) { best = opt.value; break; }
          if (!best && (v.includes(needle) || lbl.includes(needle))) {
            best = opt.value;
          }
        }
        if (best) {
          contactsSelect.value = best;
          // déclencher automatiquement l'affichage
          setTimeout(() => {
            loadDetails();
          }, 0);
        }
        initialQuery = "";
      }
    } catch (e) {
      // ignore
    }
  }

  async function loadDetails() {
    const code = contactsSelect.value;
    if (!code) return;
    try {
      const res = await fetch(API(`/technicians/${encodeURIComponent(code)}`));
      if (!res.ok) return;
      const data = await res.json();
      const d = data.details || {};
      const pr = data.pr_details || {};

      codeMagasin.textContent = d.code_magasin || "";
      libelleMagasin.textContent = d.libelle_magasin || "";
      equipe.textContent = d.equipe || "";
      responsable.textContent = d.responsable || "";
      contact.textContent = d.contact || "";
      telephone.textContent = d.telephone || "";
      email.textContent = d.email || "";
      adresse.textContent = d.adresse || "";
      // 1ère ligne : code IG (court)
      codeIg.textContent = d.code_ig || "";
      // 2ème ligne : libellé long IG
      if (libelleLongIg) libelleLongIg.textContent = d.libelle_long_ig || "";
      // 3ème ligne : adresse IG
      adresseIg.textContent = d.adresse_ig || "";

      function renderPr(prData, codeEl, codeStoreEl, ensEl, adrEl, metaEl, statutEl) {
        if (!codeEl || !prData) {
          if (codeEl) codeEl.textContent = "";
          if (codeStoreEl) codeStoreEl.textContent = "";
          if (ensEl) ensEl.textContent = "";
          if (adrEl) adrEl.textContent = "";
          if (metaEl) metaEl.textContent = "";
          if (statutEl) statutEl.textContent = "";
          return;
        }
        const code = prData.code_point_relais || "";
        const codeStore = prData.code_point_relais_store || "";
        const enseigne = prData.enseigne || "";
        const adr = prData.adresse_postale || "";
        const categoriePr = prData.categorie || "";
        const prestataire = prData.prestataire || "";
        const statut = prData.statut || "";

        codeEl.textContent = code;
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
          const periodeAbs = prData.periode_absence_a_utiliser || "";
          const bg = isOpen ? "#16a34a" : (isClosed ? "#dc2626" : "#6b7280");
          const fg = "#ffffff";
          if (statut) {
            const parts = [`Statut: ${statut}`];
            if (isClosed && periodeAbs) {
              parts.push(`Période absence: ${periodeAbs}`);
            }
            statutEl.innerHTML = `<span style="display:inline-block; padding:2px 8px; border-radius:9999px; font-size:12px; font-weight:600; background:${bg}; color:${fg};">${parts.join(" • ")}</span>`;
          } else {
            statutEl.innerHTML = "";
          }
        }
      }

      renderPr(pr.principal, prPrincipalCode, prPrincipalCodeStore, prPrincipalEns, prPrincipalAdr, prPrincipalMeta, prPrincipalStatut);
      renderPr(pr.backup, prBackupCode, prBackupCodeStore, prBackupEns, prBackupAdr, prBackupMeta, prBackupStatut);
      renderPr(pr.hors_normes, prHnCode, prHnCodeStore, prHnEns, prHnAdr, prHnMeta, prHnStatut);

      if (emptyMsg) emptyMsg.style.display = "none";
      if (detailsContent) detailsContent.style.display = "block";
    } catch (e) {
      // ignore
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

  loadContacts();
});
