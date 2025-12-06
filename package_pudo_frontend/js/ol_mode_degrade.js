document.addEventListener("DOMContentLoaded", () => {
  const techSelect = document.getElementById("omd-tech-select");
  const codeMagasin = document.getElementById("omd-code-magasin");
  const libelleMagasin = document.getElementById("omd-libelle-magasin");
  const codeTiersEl = document.getElementById("omd-code-tiers");
  const telephone = document.getElementById("omd-telephone");
  const email = document.getElementById("omd-email");
  const adresse = document.getElementById("omd-adresse");

  const btInput = document.getElementById("omd-bt");
  const dateBesoinInput = document.getElementById("omd-date-besoin");
  const commentaireInput = document.getElementById("omd-commentaire");
  const typeCommandeSelect = document.getElementById("omd-type-commande");
  const linesBody = document.getElementById("omd-lines-body");
  const addLineBtn = document.getElementById("omd-add-line");
  const validateBtn = document.getElementById("omd-validate");
  const sendMailMplcBtn = document.getElementById("omd-mail-mplc");
  const sendMailLm2sBtn = document.getElementById("omd-mail-lm2s");
  const statusDiv = document.getElementById("omd-status");

  const destTypeRadios = document.querySelectorAll("input[name='omd-destination-type']");
  const destCodeIgBlock = document.getElementById("omd-dest-code-ig");
  const destPrBlock = document.getElementById("omd-dest-pr");
  const destFreeBlock = document.getElementById("omd-dest-free");
  const madNoteEl = document.getElementById("omd-mad-note");
  const codeIgSelect = document.getElementById("omd-code-ig");
  const codeIgDatalist = document.getElementById("omd-code-ig-list");
  const codeIgAddressEl = document.getElementById("omd-code-ig-address");
  const prChoiceRadios = document.querySelectorAll("input[name='omd-pr-choice']");
  const destPrAddressEl = document.getElementById("omd-dest-pr-address");
  const storeDatalist = document.getElementById("omd-store-list");
  const freeRaisonInput = document.getElementById("omd-free-raison");
  const freeL1Input = document.getElementById("omd-free-l1");
  const freeL2Input = document.getElementById("omd-free-l2");
  const freeCpInput = document.getElementById("omd-free-cp");
  const freeVilleInput = document.getElementById("omd-free-ville");

  let technicians = [];
  let igList = [];
  let igByCode = {};
  let igLoaded = false;
  let storeMap = {};
  let currentIgAddress = "";
  let currentPrAddress = "";
  let itemLabelCache = {};
  let currentUserLogin = "";

  function getDestination(t) {
    const destTypeEl = document.querySelector("input[name='omd-destination-type']:checked");
    const destType = destTypeEl ? destTypeEl.value : "code_ig";

    if (destType === "code_ig") {
      const codeIg = codeIgSelect ? (codeIgSelect.value || "").trim() : "";
      return {
        type: "code_ig",
        code_ig: codeIg,
        adresse: currentIgAddress
      };
    }

    if (destType === "point_relais") {
      let choix = "principal";
      const prChoixEl = document.querySelector("input[name='omd-pr-choice']:checked");
      if (prChoixEl && prChoixEl.value) {
        choix = prChoixEl.value;
      }

      // On récupère le code du point relais à partir du technicien
      const codePr = choix === "hors_normes" ? (t.pr_hors_normes || t.pr_hors_norme) : t.pr_principal;

      return {
        type: "point_relais",
        choix: choix,
        code_pr: codePr || "",
        adresse: currentPrAddress
      };
    }

    // adresse_libre
    const raison = (freeRaisonInput?.value || "").trim();
    const l1 = (freeL1Input?.value || "").trim();
    const l2 = (freeL2Input?.value || "").trim();
    const cp = (freeCpInput?.value || "").trim();
    const ville = (freeVilleInput?.value || "").trim();
    return {
      type: "adresse_libre",
      raison_sociale: raison,
      adresse_ligne1: l1,
      adresse_ligne2: l2,
      code_postal: cp,
      ville: ville
    };
  }

  function updateDestinationVisibility() {
    const destTypeEl = document.querySelector("input[name='omd-destination-type']:checked");
    const destType = destTypeEl ? destTypeEl.value : "code_ig";

    if (destCodeIgBlock) destCodeIgBlock.style.display = destType === "code_ig" ? "block" : "none";
    if (destPrBlock) destPrBlock.style.display = destType === "point_relais" ? "block" : "none";
    if (destFreeBlock) destFreeBlock.style.display = destType === "adresse_libre" ? "block" : "none";
  }

  async function loadPrAddressForCurrentSelection() {
    const destTypeEl = document.querySelector("input[name='omd-destination-type']:checked");
    const destType = destTypeEl ? destTypeEl.value : "code_ig";
    if (destType !== "point_relais") {
      currentPrAddress = "";
      if (destPrAddressEl) destPrAddressEl.textContent = "";
      return;
    }

    const idx = parseInt(techSelect.value || "0", 10);
    const t = technicians[idx];
    if (!t) {
      currentPrAddress = "";
      if (destPrAddressEl) destPrAddressEl.textContent = "";
      return;
    }

    let choix = "principal";
    const prChoixEl = document.querySelector("input[name='omd-pr-choice']:checked");
    if (prChoixEl && prChoixEl.value) {
      choix = prChoixEl.value;
    }

    const codePr = choix === "hors_normes" ? (t.pr_hors_normes || t.pr_hors_norme) : t.pr_principal;
    if (!codePr) {
      currentPrAddress = "";
      if (destPrAddressEl) destPrAddressEl.textContent = "";
      return;
    }

    try {
      const res = await fetch(API(`/technicians/ol_pudo_address/${encodeURIComponent(codePr)}`));
      if (!res.ok) {
        currentPrAddress = "";
        if (destPrAddressEl) destPrAddressEl.textContent = "";
        return;
      }
      const data = await res.json();
      const adr = data.adresse_postale || "";
      const ens = data.enseigne || "";
      currentPrAddress = adr;
      if (destPrAddressEl) {
        const idx = parseInt(techSelect.value || "0", 10);
        const t = technicians[idx];
        let choix = "principal";
        const prChoixEl = document.querySelector("input[name='omd-pr-choice']:checked");
        if (prChoixEl && prChoixEl.value) {
          choix = prChoixEl.value;
        }
        const codePr = t
          ? (choix === "hors_normes" ? (t.pr_hors_normes || t.pr_hors_norme) : t.pr_principal)
          : "";

        const baseAdr = ens ? `${ens} - ${adr}` : adr;
        destPrAddressEl.textContent = codePr ? `${codePr} - ${baseAdr}` : baseAdr;
      }
    } catch (e) {
      currentPrAddress = "";
      if (destPrAddressEl) destPrAddressEl.textContent = "";
    }
  }

  async function loadStores() {
    try {
      const res = await fetch(API("/technicians/ol_stores"));
      if (!res.ok) return;
      const data = await res.json();
      const stores = data.stores || [];
      stores
        .filter((s) => {
          const type = (s.type_de_depot || "").toLowerCase();
          const codeMag = String(s.code_magasin || "");
          const statut = s.statut;
          if (!codeMag) return false;
          if (!type) return false;
          if (!(type === "national" || type === "local")) return false;
          // Ne retenir que les magasins avec statut 0
          if (!(statut === 0 || statut === "0")) return false;
          // Restreindre aux codes magasin expéditeur commençant par "M"
          return codeMag.startsWith("M");
        })
        .forEach((store) => {
          const code = store.code_magasin;
          if (!code) return;
          const lib = store.libelle_magasin || "";
          const adr = store.adresse_postale || "";
          const adr1 = store.adresse1 || "";
          const adr2 = store.adresse2 || "";
          const cp = store.code_postal || "";
          const ville = store.ville || "";
          const codeTiers = store.code_tiers_daher || "";

          storeMap[code] = {
            libelle_magasin: lib,
            adresse_postale: adr,
            adresse1: adr1,
            adresse2: adr2,
            code_postal: cp,
            ville: ville,
            code_tiers_daher: codeTiers,
          };

          // Alimenter la datalist globale des magasins
          if (storeDatalist) {
            const opt = document.createElement("option");
            opt.value = code;
            const parts = [code];
            if (lib) parts.push(lib);
            if (adr) parts.push(adr);
            opt.label = parts.join(" - ");
            storeDatalist.appendChild(opt);
          }
        });
    } catch (e) {
      storeMap = {};
    }
  }

  function updateCodeIgAddress() {
    if (!codeIgSelect) return;
    const code = (codeIgSelect.value || "").trim().toUpperCase();
    if (!code) {
      currentIgAddress = "";
      if (codeIgAddressEl) codeIgAddressEl.textContent = "";
      return;
    }
    const ig = igByCode[code];
    if (!ig) {
      currentIgAddress = "";
      if (codeIgAddressEl) codeIgAddressEl.textContent = "";
      return;
    }
    currentIgAddress = ig.adresse_postale || "";
    if (codeIgAddressEl) {
      const lbl = ig.libelle_long_ig || "";
      const adr = ig.adresse_postale || "";
      codeIgAddressEl.textContent = lbl ? `${lbl} - ${adr}` : adr;
    }
  }

  function enforceDestinationRules() {
    const isUrgent = typeCommandeSelect && typeCommandeSelect.value === "URGENT";
    const isMad = typeCommandeSelect && typeCommandeSelect.value === "MAD";

    // Gestion de l'état désactivé/grisé pour MAD
    if (destTypeRadios && destTypeRadios.length > 0) {
      Array.from(destTypeRadios).forEach((r) => {
        const label = r.closest("label");
        if (isMad) {
          r.disabled = true;
          if (label) {
            label.style.opacity = "0.5";
            label.style.cursor = "not-allowed";
          }
        } else {
          // En dehors du mode MAD, on réactive par défaut, la logique URGENT s'applique ensuite.
          r.disabled = false;
          if (label) {
            label.style.opacity = "1";
            label.style.cursor = "pointer";
          }
        }
      });
    }

    // Si MAD, on force simplement un choix existant (par ex. Code IG) et on cache les blocs de saisie.
    if (isMad && destTypeRadios && destTypeRadios.length > 0) {
      const codeIgRadio = Array.from(destTypeRadios).find(r => r.value === "code_ig");
      if (codeIgRadio) {
        codeIgRadio.checked = true;
      }
      // On masque tous les blocs de champs de destination.
      if (destCodeIgBlock) destCodeIgBlock.style.display = "none";
      if (destPrBlock) destPrBlock.style.display = "none";
      if (destFreeBlock) destFreeBlock.style.display = "none";
      if (madNoteEl) {
        madNoteEl.style.display = "block";
        madNoteEl.textContent = "En mode MAD, l'adresse de livraison correspond au(x) magasin(s) expéditeur(s).";
      }
      return;
    }

    if (madNoteEl) {
      madNoteEl.style.display = "none";
      madNoteEl.textContent = "";
    }

    // Logique URGENT : on interdit uniquement "Point relais".
    const prRadio = Array.from(destTypeRadios || []).find(r => r.value === "point_relais");
    if (prRadio) {
      prRadio.disabled = isUrgent;
      const prLabel = prRadio.closest("label");
      if (prLabel) {
        prLabel.style.opacity = isUrgent ? "0.5" : "1";
      }
      if (isUrgent && prRadio.checked) {
        // Bascule automatiquement sur Code IG si Point relais était sélectionné.
        const codeIgRadio = Array.from(destTypeRadios).find(r => r.value === "code_ig");
        if (codeIgRadio) {
          codeIgRadio.checked = true;
        }
      }
    }

    updateDestinationVisibility();
  }

  function renderTechnicians() {
    techSelect.innerHTML = "";
    technicians.forEach((t, idx) => {
      const opt = document.createElement("option");
      opt.value = String(idx);
      const name = t.contact || "(contact inconnu)";
      const code = t.code_magasin || "?";
      opt.textContent = name + " (" + code + ")";
      techSelect.appendChild(opt);
    });
    if (technicians.length > 0) {
      techSelect.value = "0";
      updateTechnicianDetails();
    }
  }

  async function searchIgs(query) {
    if (!codeIgDatalist) return;
    const q = (query || "").trim();
    if (q.length < 2) {
      codeIgDatalist.innerHTML = "";
      igByCode = {};
      return;
    }
    try {
      const res = await fetch(API(`/technicians/ol_igs_search?q=${encodeURIComponent(q)}&limit=50`));
      if (!res.ok) return;
      const data = await res.json();
      const igs = data.igs || [];
      igByCode = {};
      codeIgDatalist.innerHTML = "";
      igs.forEach((ig) => {
        const code = String(ig.code_ig || "");
        const lbl = ig.libelle_long_ig || "";
        const opt = document.createElement("option");
        opt.value = code;
        opt.label = lbl ? `${code} - ${lbl}` : code;
        codeIgDatalist.appendChild(opt);
        if (code) {
          igByCode[code.toUpperCase()] = ig;
        }
      });
    } catch (e) {
      // ignore
    }
  }

  function debounce(fn, delay) {
    let timeoutId;
    return (...args) => {
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
      timeoutId = setTimeout(() => {
        fn(...args);
      }, delay);
    };
  }

  const debouncedSearchIgs = debounce(searchIgs, 300);

  async function loadTechnicians() {
    try {
      const res = await fetch(API("/technicians/ol_technicians"));
      if (!res.ok) {
        return;
      }
      const data = await res.json();
      technicians = data.technicians || [];
      renderTechnicians();
    } catch (e) {
      // en cas d'erreur, on laisse la liste vide
    }
  }

  function updateTechnicianDetails() {
    const idx = parseInt(techSelect.value || "0", 10);
    const t = technicians[idx];
    if (!t) return "";
    codeMagasin.textContent = t.code_magasin || "";
    libelleMagasin.textContent = t.libelle_magasin || "";
    let techCodeTiers = t.code_tiers_daher || "";
    if (!techCodeTiers && t.code_magasin && storeMap[t.code_magasin]) {
      techCodeTiers = storeMap[t.code_magasin].code_tiers_daher || "";
    }
    if (codeTiersEl) {
      codeTiersEl.textContent = techCodeTiers;
    }
    telephone.textContent = t.telephone || "";
    email.textContent = t.email || "";
    adresse.textContent = t.adresse || "";

    loadPrAddressForCurrentSelection();
  }

  function addLine(initial) {
    const tr = document.createElement("tr");
    tr.className = "omd-line-row";

    const tdItem = document.createElement("td");
    const inputItem = document.createElement("input");
    inputItem.type = "text";
    inputItem.className = "omd-item-code";
    inputItem.value = initial && initial.code_article ? initial.code_article : "";
    inputItem.style.width = "100%";
    tdItem.appendChild(inputItem);

    const tdLabel = document.createElement("td");
    const spanLabel = document.createElement("span");
    spanLabel.className = "omd-item-label";
    spanLabel.textContent = initial && initial.libelle ? initial.libelle : "";
    tdLabel.appendChild(spanLabel);

    const spanFlag = document.createElement("div");
    spanFlag.className = "omd-item-flag";
    spanFlag.style.fontSize = "0.75rem";
    spanFlag.style.color = "red";
    if (initial && initial.hors_norme) {
      spanFlag.textContent = "article hors norme";
    }
    tdLabel.appendChild(spanFlag);

    const tdQty = document.createElement("td");
    const inputQty = document.createElement("input");
    inputQty.type = "number";
    inputQty.min = "0";
    inputQty.step = "1";
    inputQty.value = initial && initial.quantite ? initial.quantite : "";
    inputQty.style.width = "100%";
    tdQty.appendChild(inputQty);

    const tdStore = document.createElement("td");
    const inputStore = document.createElement("input");
    inputStore.type = "text";
    inputStore.className = "omd-store-code";
    inputStore.value = initial && initial.code_magasin ? initial.code_magasin : "";
    inputStore.style.width = "100%";
    if (storeDatalist) {
      inputStore.setAttribute("list", "omd-store-list");
    }
    tdStore.appendChild(inputStore);

    const tdActions = document.createElement("td");
    tdActions.style.verticalAlign = "top";
    const btnDel = document.createElement("button");
    btnDel.type = "button";
    btnDel.textContent = "Supprimer";
    btnDel.addEventListener("click", () => {
      // Supprime la ligne principale et la ligne d'info expédition associée
      const next = tr.nextElementSibling;
      if (next && next.classList.contains("omd-exp-row")) {
        linesBody.removeChild(next);
      }
      linesBody.removeChild(tr);
    });
    tdActions.appendChild(btnDel);

    tr.appendChild(tdItem);
    tr.appendChild(tdLabel);
    tr.appendChild(tdQty);
    tr.appendChild(tdStore);
    tr.appendChild(tdActions);

    // Ligne supplémentaire pour l'adresse d'expédition + lien Google Maps
    const expTr = document.createElement("tr");
    expTr.className = "omd-exp-row";
    const expTd = document.createElement("td");
    expTd.colSpan = 5;
    const expInfoDiv = document.createElement("div");
    expInfoDiv.className = "omd-exp-info";
    expInfoDiv.style.marginTop = "0.15rem";
    expInfoDiv.style.fontSize = "0.8rem";

    const expAddrSpan = document.createElement("span");
    expAddrSpan.className = "omd-exp-address";
    expInfoDiv.appendChild(expAddrSpan);

    const expLink = document.createElement("a");
    expLink.href = "#";
    expLink.textContent = "Itinéraire Google Maps";
    expLink.className = "omd-exp-link";
    expLink.style.marginLeft = "0.5rem";
    expLink.target = "_blank";
    expLink.rel = "noopener noreferrer";
    expLink.addEventListener("click", (ev) => {
      const url = openGoogleMapsForRow(tr);
      if (!url) {
        ev.preventDefault();
        return;
      }
      // On transforme dynamiquement le lien en véritable URL Google Maps
      expLink.href = url;
    });
    expInfoDiv.appendChild(expLink);

    expTd.appendChild(expInfoDiv);
    expTr.appendChild(expTd);

    linesBody.appendChild(tr);
    linesBody.appendChild(expTr);
    updateExpeditionInfoForRow(tr);
  }

  function getLines() {
    const rows = Array.from(linesBody.querySelectorAll("tr.omd-line-row"));
    return rows.map((tr) => {
      const inputs = tr.querySelectorAll("input");
      const labelEl = tr.querySelector(".omd-item-label");
      const flagEl = tr.querySelector(".omd-item-flag");
      return {
        code_article: inputs[0] ? inputs[0].value.trim() : "",
        libelle: labelEl ? labelEl.textContent || "" : "",
        quantite: inputs[1] ? Number(inputs[1].value || "0") : 0,
        code_magasin: inputs[2] ? inputs[2].value.trim() : "",
        hors_norme: flagEl ? !!(flagEl.textContent && flagEl.textContent.trim()) : false,
      };
    });
  }

  function updateItemLabel(inputEl) {
    if (!inputEl) return;
    const tr = inputEl.closest("tr");
    if (!tr) return;
    const labelEl = tr.querySelector(".omd-item-label");
    if (!labelEl) return;
    const raw = (inputEl.value || "").trim();
    const code = raw.toUpperCase();
    if (!code) {
      labelEl.textContent = "";
      return;
    }

    // Si déjà en cache, on évite un nouvel appel API.
    if (itemLabelCache[code]) {
      labelEl.textContent = itemLabelCache[code];
      return;
    }

    // Indication visuelle le temps de la requête.
    labelEl.textContent = "Recherche article...";

    fetch(API(`/items/${encodeURIComponent(code)}/details`))
      .then((res) => {
        if (!res.ok) return null;
        return res.json();
      })
      .then(async (data) => {
        let finalLabel = "";
        let isHorsNormeGlobal = false;

        // Aides pour les indicateurs (hors norme / fragile / affrètement)
        const isOui = (v) => {
          if (v === null || v === undefined) return false;
          const s = String(v).trim().toUpperCase();
          return s === "OUI";
        };
        const isY = (v) => {
          if (v === null || v === undefined) return false;
          const s = String(v).trim().toUpperCase();
          return s === "Y";
        };

        if (data && data.item) {
          const item = data.item || {};

          // Si l'article est hors norme / fragile / affrètement, on force le libellé générique
          // Règle métier :
          //  - hors norme : colonne article_hors_norme (ou article_hors_normes) = "OUI"
          //  - fragile   : colonne fragile = "Y"
          //  - affrètement : colonne affretement = "Y"
          const flagHorsNorme = isOui(item.article_hors_norme) || isOui(item.article_hors_normes);
          const flagFragile = isY(item.fragile);
          const flagAffretement = isY(item.affretement);

          const isHorsNorme = flagHorsNorme || flagFragile || flagAffretement;

          if (isHorsNorme) {
            isHorsNormeGlobal = true;
          }

          const libelle = item.libelle_court_article || item.libelle_long_article || "";
          if (libelle) {
            finalLabel = libelle;
          }
        }

        // Fallback si aucun item ou libellé non renseigné: recherche côté API
        if (!finalLabel) {
          try {
            const searchRes = await fetch(API("/items/search"), {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ q: code, filters: {}, limit: 1 }),
            });
            if (searchRes.ok) {
              const searchData = await searchRes.json();
              const rows = searchData.rows || [];
              if (rows.length > 0) {
                const row = rows[0] || {};

                // Appliquer aussi la logique hors norme / fragile / affrètement sur la ligne de recherche
                const flagHorsNormeSearch =
                  isOui(row.article_hors_norme) ||
                  isOui(row.article_hors_normes) ||
                  isOui(row.article_hors_normes_right);
                const flagFragileSearch = isY(row.fragile);
                const flagAffretementSearch = isY(row.affretement);

                const isHorsNormeSearch =
                  flagHorsNormeSearch || flagFragileSearch || flagAffretementSearch;

                if (isHorsNormeSearch) {
                  isHorsNormeGlobal = true;
                }

                const lib = row.libelle_court_article || row.libelle_long_article || "";
                if (lib) {
                  finalLabel = lib;
                }
              }
            }
          } catch (e) {
            // ignore, on gardera éventuellement un label vide
          }
        }

        const flagEl = tr.querySelector(".omd-item-flag");

        if (!finalLabel) {
          // En dernier recours, on n'affiche rien plutôt que le code.
          labelEl.textContent = "";
          if (flagEl) flagEl.textContent = "";
          return;
        }

        itemLabelCache[code] = finalLabel;

        // On vérifie que le champ contient toujours le même code avant d'afficher.
        const currentVal = (inputEl.value || "").trim().toUpperCase();
        if (currentVal === code) {
          labelEl.textContent = finalLabel;
          if (flagEl) {
            flagEl.textContent = isHorsNormeGlobal ? "article hors norme" : "";
          }
        }
      })
      .catch(() => {
        labelEl.textContent = "";
      });
  }

  function updateExpeditionInfoForRow(tr) {
    if (!tr) return;
    const inputs = tr.querySelectorAll("input");
    const storeInput = inputs[2];
    const expRow = tr.nextElementSibling;
    const addrSpan = expRow ? expRow.querySelector(".omd-exp-address") : null;
    if (!storeInput || !addrSpan) return;

    const codeMag = (storeInput.value || "").trim();
    if (!codeMag || !storeMap[codeMag]) {
      addrSpan.textContent = "";
      return;
    }

    const store = storeMap[codeMag];
    const adr1 = store.adresse1 || "";
    const adr2 = store.adresse2 || "";
    const adr = store.adresse_postale || "";
    const cp = store.code_postal || "";
    const ville = store.ville || "";
    const lib = store.libelle_magasin || "";
    const parts = [];
    if (lib) parts.push(lib);
    if (adr1) parts.push(adr1);
    if (adr2) parts.push(adr2);
    // Si pas d'adr1/adr2, on se rabat sur adresse_postale
    if (!adr1 && !adr2 && adr) parts.push(adr);
    // Ajout code postal + ville si présents
    const cpVille = [cp, ville].map((x) => String(x || "").trim()).filter(Boolean).join(" ");
    if (cpVille) parts.push(cpVille);
    addrSpan.textContent = parts.join(" – ");
  }

  function refreshAllExpeditionInfo() {
    if (!linesBody) return;
    const rows = Array.from(linesBody.querySelectorAll("tr.omd-line-row"));
    rows.forEach((tr) => {
      updateExpeditionInfoForRow(tr);
    });
  }

  function openGoogleMapsForRow(tr) {
    if (!tr) return "";

    // Origine : adresse du magasin expéditeur de la ligne
    const inputs = tr.querySelectorAll("input");
    const storeInput = inputs[2];
    if (!storeInput) return "";
    const codeMag = (storeInput.value || "").trim();
    const store = codeMag ? storeMap[codeMag] : null;
    const originAddr = store && store.adresse_postale ? String(store.adresse_postale).trim() : "";

    // Destination :
    // - En mode MAD, la destination est le magasin expéditeur lui-même (adresse identique à l'origine).
    // - Sinon, on utilise l'adresse de livraison courante.
    let destAddr = "";
    const typeCmd = typeCommandeSelect && typeCommandeSelect.value;

    if ((typeCmd || "").toUpperCase() === "MAD") {
      destAddr = originAddr;
    } else {
      const idx = parseInt(techSelect.value || "0", 10);
      const t = technicians[idx];
      if (!t) return "";
      const dest = getDestination(t) || {};

      if (dest.type === "code_ig" || dest.type === "point_relais") {
        destAddr = String(dest.adresse || "").trim();
      } else if (dest.type === "adresse_libre") {
        const l1 = dest.adresse_ligne1 || "";
        const l2 = dest.adresse_ligne2 || "";
        const cp = dest.code_postal || "";
        const ville = dest.ville || "";
        destAddr = [l1, l2, cp, ville].map((x) => String(x || "").trim()).filter(Boolean).join(" ");
      }
    }

    if (!originAddr || !destAddr) {
      return "";
    }

    const url = "https://www.google.com/maps/dir/?api=1" +
      "&origin=" + encodeURIComponent(originAddr) +
      "&destination=" + encodeURIComponent(destAddr) +
      "&travelmode=driving";

    return url;
  }

  function validate() {
    statusDiv.textContent = "";
    const bt = (btInput.value || "").trim();
    const dateBesoinRaw = (dateBesoinInput && dateBesoinInput.value) ? dateBesoinInput.value : "";
    const commentaireLibre = (commentaireInput && commentaireInput.value) ? commentaireInput.value.trim() : "";
    const typeCommande = typeCommandeSelect.value;
    const idx = parseInt(techSelect.value || "0", 10);
    const t = technicians[idx];
    const lines = getLines();

    if (!bt) {
      statusDiv.textContent = "Merci de saisir un numéro de BT.";
      return;
    }
    if (!t) {
      statusDiv.textContent = "Merci de sélectionner un technicien.";
      return;
    }
    // On ne considère comme ligne candidate que celles avec un code article renseigné
    const nonEmptyLines = lines.filter(l => (l.code_article || "").trim() !== "");
    if (nonEmptyLines.length === 0) {
      statusDiv.textContent = "Merci de saisir au moins une ligne de commande avec un code article.";
      return;
    }

    // Règle métier : pour chaque ligne article, le code magasin expéditeur est obligatoire
    const missingStore = nonEmptyLines.find(l => !(l.code_magasin || "").trim());
    if (missingStore) {
      statusDiv.textContent = "Merci de renseigner un code magasin expéditeur pour chaque ligne de code article.";
      return;
    }

    const destination = getDestination(t);

    // Règle métier : la destination doit être correctement renseignée
    if (destination.type === "code_ig") {
      const codeIg = (destination.code_ig || "").trim();
      if (!codeIg) {
        statusDiv.textContent = "Merci de renseigner un code IG pour l'adresse de livraison.";
        return;
      }
    } else if (destination.type === "adresse_libre") {
      // Raison sociale et adresse ligne 2 facultatives, on impose seulement adresse, CP, ville
      if (!destination.adresse_ligne1 || !destination.code_postal || !destination.ville) {
        statusDiv.textContent = "Merci de compléter l'adresse libre (adresse, code postal, ville).";
        return;
      }
    }

    const payload = {
      bt: bt,
      type_commande: typeCommande,
      date_besoin: dateBesoinRaw,
      commentaire_libre: commentaireLibre,
      technicien: t,
      destination: destination,
      lignes: nonEmptyLines
    };
    return payload;
  }

  function buildEmailBody(payload) {
    const now = new Date();
    const pad = (n) => String(n).padStart(2, "0");
    const dateStr = `${pad(now.getDate())}/${pad(now.getMonth() + 1)}/${now.getFullYear()} ${pad(now.getHours())}:${pad(now.getMinutes())}`;

    const login = currentUserLogin || "";

    const dest = payload.destination || {};
    const tech = payload.technicien || {};
    const dateBesoinRaw = payload.date_besoin || "";
    const commentaireLibre = payload.commentaire_libre || "";

    // Mise en forme simple de la date/heure de besoin (valeur brute si non renseignée autrement)
    let dateBesoinText = "";
    if (dateBesoinRaw) {
      // datetime-local renvoie un format "YYYY-MM-DDTHH:MM" ; on le rend plus lisible
      const [d, h] = String(dateBesoinRaw).split("T");
      if (d) {
        const [y, m, day] = d.split("-");
        const human = [day, m, y].filter(Boolean).join("/");
        dateBesoinText = h ? `${human} ${h}` : human;
      } else {
        dateBesoinText = dateBesoinRaw;
      }
    }
    let destText = "";
    if (dest.type === "code_ig") {
      const codeIg = dest.code_ig || "";
      const adr = dest.adresse || "";
      destText = `Code IG : ${codeIg} / Adresse : ${adr}`.trim();
    } else if (dest.type === "point_relais") {
      const choix = dest.choix || "principal";
      const codePr = dest.code_pr || "";
      const adr = dest.adresse || "";
      destText = `Point relais${codePr ? ` (${codePr} - ${choix})` : ` (${choix})`}${adr ? ` / Adresse : ${adr}` : ""}`;
    } else if (dest.type === "adresse_libre") {
      destText = `Raison sociale : ${dest.raison_sociale || ""}\n${dest.adresse_ligne1 || ""}\n${dest.adresse_ligne2 || ""}\n${dest.code_postal || ""} ${dest.ville || ""}`;
    }
    if (!destText || !destText.trim()) {
      destText = "(adresse de livraison non renseignée)";
    }

    const lignes = payload.lignes || [];

    const lignesText = lignes
      .map((l, idx) => {
        const codeMag = l.code_magasin || "";
        const base = `Ligne ${idx + 1} : ${l.code_article || ""} - ${l.libelle || ""} - Qté : ${l.quantite || 0} - Code magasin : ${codeMag}`;
        const flag = l.hors_norme ? " [article hors norme]" : "";
        return base + flag;
      })
      .join("\n");

    // Adresse(s) d'expédition : on agrège les magasins distincts avec leurs infos
    const expAddresses = [];
    const seenExp = new Set();
    lignes.forEach((l) => {
      const codeMag = l.code_magasin || "";
      if (!codeMag) return;
      const store = storeMap[codeMag];
      if (!store) return;
      if (seenExp.has(codeMag)) return;
      seenExp.add(codeMag);

      const lib = store.libelle_magasin || "";
      const adr1 = store.adresse1 || "";
      const adr2 = store.adresse2 || "";
      const adrExp = store.adresse_postale || "";
      const cp = store.code_postal || "";
      const ville = store.ville || "";
      const codeTiers = store.code_tiers_daher || "";

      let line = `- Code magasin : ${codeMag}`;
      if (lib) {
        line += ` / Libellé : ${lib}`;
      }
      if (codeTiers) {
        line += ` / Code tiers Daher : ${codeTiers}`;
      }
      if (adr1) {
        line += ` / Adresse1 : ${adr1}`;
      }
      if (adr2) {
        line += ` / Adresse2 : ${adr2}`;
      }
      if (adrExp && !adr1 && !adr2) {
        line += ` / Adresse : ${adrExp}`;
      }
      if (cp || ville) {
        line += ` / CP/Ville : ${cp || ""} ${ville || ""}`.trim();
      }
      expAddresses.push(line);
    });
    const expText = expAddresses.join("\n") || "";

    // En mode MAD, l'adresse de livraison doit correspondre aux magasins expéditeurs
    if ((payload.type_commande || "").toUpperCase() === "MAD") {
      destText = expText || "(adresse de livraison = magasin(s) expéditeur(s))";
    }

    // Construction d'un lien Google Maps (origine = premier magasin expéditeur, destination = adresse de livraison)
    let googleMapsUrl = "";
    if (lignes.length > 0) {
      const firstWithStore = lignes.find(l => (l.code_magasin || "").trim());
      if (firstWithStore) {
        const codeMag = (firstWithStore.code_magasin || "").trim();
        const store = codeMag ? storeMap[codeMag] : null;
        const originAddr = store && store.adresse_postale ? String(store.adresse_postale).trim() : "";

        let destAddr = "";
        const typeCmd = (payload.type_commande || "").toUpperCase();

        if (typeCmd === "MAD") {
          destAddr = originAddr;
        } else if (dest.type === "code_ig" || dest.type === "point_relais") {
          destAddr = String(dest.adresse || "").trim();
        } else if (dest.type === "adresse_libre") {
          const l1 = dest.adresse_ligne1 || "";
          const l2 = dest.adresse_ligne2 || "";
          const cp = dest.code_postal || "";
          const ville = dest.ville || "";
          destAddr = [l1, l2, cp, ville].map(x => String(x || "").trim()).filter(Boolean).join(" ");
        }

        if (originAddr && destAddr) {
          googleMapsUrl = "https://www.google.com/maps/dir/?api=1" +
            "&origin=" + encodeURIComponent(originAddr) +
            "&destination=" + encodeURIComponent(destAddr) +
            "&travelmode=driving";
        }
      }
    }

    // Compléter les infos magasin du technicien à partir de storeMap si besoin
    let techCodeMag = tech.code_magasin || "";
    // Si le technicien n'a pas de code magasin, on prend celui de la première ligne (magasin d'expédition principal)
    if (!techCodeMag && lignes.length > 0) {
      techCodeMag = lignes[0].code_magasin || "";
    }

    let techLibMag = tech.libelle_magasin || "";
    let techCodeTiers = tech.code_tiers_daher || "";
    if (techCodeMag && (!techLibMag || !techCodeTiers)) {
      const techStore = storeMap[techCodeMag];
      if (techStore) {
        if (!techLibMag) techLibMag = techStore.libelle_magasin || "";
        if (!techCodeTiers) techCodeTiers = techStore.code_tiers_daher || "";
      }
    }

    const bodyLines = [
      "*** ORDRE DE LIVRAISON EN MODE DEGRADE ***",
      "",
      "ENTETE ORDRE DE LIVRAISON",
      `Date/heure de la commande : ${dateStr}`,
      `Login utilisateur : ${login}`,
      `Numéro de BT : ${payload.bt || ""}`,
      `Date/heure de besoin : ${dateBesoinText || "(non renseignée)"}`,
      `Type de commande : ${payload.type_commande || ""}`,
      "",
      "COMMENTAIRE :",
      commentaireLibre || "(aucun)",
      "",
      "CONTACT TECHNICIEN :",
      `Nom : ${tech.contact || tech.libelle_magasin || ""}`,
      `Téléphone : ${tech.telephone || ""}`,
      `Code magasin : ${techCodeMag}`,
      `Libellé magasin : ${techLibMag}`,
      `Code tiers Daher : ${techCodeTiers}`,
      "",
      "ADRESSE D'EXPÉDITION :",
      expText || "(non renseignée)",
      "",
      "ADRESSE DE LIVRAISON :",
      destText,
      "",
    ];

    // Ajout d'une consigne de contact pour les livraisons directes (code IG ou adresse libre)
    const destType = dest.type || "";
    if (destType === "code_ig" || destType === "adresse_libre") {
      const tel = tech.telephone || "";
      const telText = tel ? ` ${tel}` : "";
      bodyLines.push(`Contacter le technicien 30 min avant votre arrivée${telText}`);
      bodyLines.push("");
    }

    bodyLines.push(
      "LIGNES DE COMMANDE :",
      lignesText
    );

    // Ajout éventuel du lien Google Maps en fin de mail
    if (googleMapsUrl) {
      bodyLines.push("");
      bodyLines.push("LIEN GOOGLE MAP :");
      bodyLines.push(googleMapsUrl);
    }

    return bodyLines.join("\n");
  }

  function sendMail(mode) {
    const payload = validate();
    if (!payload) return;

    // S'assure que l'adresse affichée à l'écran est cohérente avant d'ouvrir le mail
    updateCodeIgAddress();
    loadPrAddressForCurrentSelection();

    // Helper pour construire l'objet du mail avec préfixe, BT, type de commande et tag destinataire
    function buildSubject(tag) {
      const parts = ["[MODE DEGRADE]", "Commande OL dégradé"];
      if (payload.bt) {
        parts.push(`BT ${payload.bt}`);
      }
      const typeCmd = (payload.type_commande || "").toUpperCase();
      if (typeCmd) {
        parts.push(typeCmd);
      }
      if (tag) {
        parts.push(tag);
      }
      return encodeURIComponent(parts.join(" - "));
    }

    // Réinitialisation de l'affichage des boutons spécifiques
    if (sendMailMplcBtn) sendMailMplcBtn.style.display = "none";
    if (sendMailLm2sBtn) sendMailLm2sBtn.style.display = "none";

    // Détermination des destinataires en fonction des magasins expéditeurs
    const lignes = payload.lignes || [];
    const hasLines = lignes.length > 0;
    const allMplc = hasLines && lignes.every(l => (l.code_magasin || "").trim().toUpperCase() === "MPLC");
    const anyMplc = hasLines && lignes.some(l => (l.code_magasin || "").trim().toUpperCase() === "MPLC");

    // Pré-calcul des sous-ensembles pour faciliter les modes dédiés
    const lignesMplc = lignes.filter(l => (l.code_magasin || "").trim().toUpperCase() === "MPLC");
    const lignesAutres = lignes.filter(l => (l.code_magasin || "").trim().toUpperCase() !== "MPLC");

    // Helper local pour ouvrir un mail pour un sous-ensemble de lignes
    function openMailForLines(linesSubset, mode) {
      const subPayload = { ...payload, lignes: linesSubset };
      const body = encodeURIComponent(buildEmailBody(subPayload));

      const importance = "&X-Priority=1%20(Highest)&Importance=High";

      if (mode === "mplc") {
        const subject = buildSubject("DAHER");
        const to = encodeURIComponent("ordotdf@daher.com; t.robas@daher.com");
        const cc = encodeURIComponent("logistique_pilotage_operationnel@tdf.fr; sophie.khayat@tdf.fr; francis.khaled-khodja@tdf.fr");
        const mailto = `mailto:${to}?cc=${cc}&subject=${subject}&body=${body}${importance}`;
        window.location.href = mailto;
      } else if (mode === "lm2s") {
        const subject = buildSubject("LM2S");
        const to = encodeURIComponent("serviceclients@lm2s.fr");
        const cc = encodeURIComponent("logistique_pilotage_operationnel@tdf.fr; sophie.khayat@tdf.fr; francis.khaled-khodja@tdf.fr");
        const mailto = `mailto:${to}?cc=${cc}&subject=${subject}&body=${body}${importance}`;
        window.location.href = mailto;
      } else {
        const subject = buildSubject("");
        const mailto = `mailto:?subject=${subject}&body=${body}${importance}`;
        window.location.href = mailto;
      }
    }

    if (!hasLines) {
      // Ne devrait pas arriver car validate() l'empêche déjà, mais on garde un fallback sûr
      const body = encodeURIComponent(buildEmailBody(payload));
      const subject = buildSubject("");
      const importance = "&X-Priority=1%20(Highest)&Importance=High";
      const mailto = `mailto:?subject=${subject}&body=${body}${importance}`;
      window.location.href = mailto;
      return;
    }
    // Si un mode spécifique est demandé, on envoie uniquement le sous-ensemble correspondant
    if (mode === "mplc") {
      if (!lignesMplc.length) {
        statusDiv.textContent = "Aucune ligne avec code magasin MPLC dans la commande.";
        return;
      }
      openMailForLines(lignesMplc, "mplc");
      return;
    }
    if (mode === "lm2s") {
      if (!lignesAutres.length) {
        statusDiv.textContent = "Aucune ligne avec code magasin différent de MPLC dans la commande.";
        return;
      }
      openMailForLines(lignesAutres, "lm2s");
      return;
    }

    // Mode automatique (clic sur "Valider l'ordre de livraison")
    if (allMplc) {
      // 1) Toutes les lignes ont MPLC comme magasin expéditeur -> un seul mail Daher
      openMailForLines(lignes, "mplc");
    } else if (hasLines && !anyMplc) {
      // 2) Aucune ligne n'a MPLC -> un seul mail LM2S
      openMailForLines(lignes, "lm2s");
    } else {
      // 3) Cas mixte : on ne déclenche pas d'envoi automatique, on affiche les deux boutons
      statusDiv.textContent = "Cas mixte détecté : utilisez les boutons 'Mail Daher (lignes MPLC)' et 'Mail LM2S (autres lignes)'.";
      if (sendMailMplcBtn) sendMailMplcBtn.style.display = "inline-block";
      if (sendMailLm2sBtn) sendMailLm2sBtn.style.display = "inline-block";
    }
  }

  async function loadCurrentUserLogin() {
    try {
      const res = await fetch(API("/auth/me"), {
        method: "GET",
        credentials: "include",
      });
      if (!res.ok) return;
      const data = await res.json();
      const login = (data && data.login) ? String(data.login).trim() : "";
      currentUserLogin = login;
    } catch (e) {
      currentUserLogin = "";
    }
  }

  if (techSelect) {
    techSelect.addEventListener("change", () => {
      updateTechnicianDetails();
    });
  }
  if (addLineBtn) {
    addLineBtn.addEventListener("click", () => {
      addLine();
    });
  }
  if (validateBtn) {
    validateBtn.addEventListener("click", () => {
      sendMail();
    });
  }
  if (sendMailMplcBtn) {
    sendMailMplcBtn.addEventListener("click", () => {
      sendMail("mplc");
    });
  }
  if (sendMailLm2sBtn) {
    sendMailLm2sBtn.addEventListener("click", () => {
      sendMail("lm2s");
    });
  }

  if (destTypeRadios && destTypeRadios.length > 0) {
    destTypeRadios.forEach((r) => {
      r.addEventListener("change", () => {
        updateDestinationVisibility();
        loadPrAddressForCurrentSelection();
      });
    });
  }

  if (prChoiceRadios && prChoiceRadios.length > 0) {
    prChoiceRadios.forEach((r) => {
      r.addEventListener("change", () => {
        loadPrAddressForCurrentSelection();
      });
    });
  }

  if (codeIgSelect) {
    codeIgSelect.addEventListener("input", () => {
      const q = (codeIgSelect.value || "").trim();
      debouncedSearchIgs(q);
      updateCodeIgAddress();
    });
  }

  if (typeCommandeSelect) {
    typeCommandeSelect.addEventListener("change", () => {
      enforceDestinationRules();
      loadPrAddressForCurrentSelection();
    });
  }

  loadCurrentUserLogin();
  loadTechnicians();
  loadStores();
  if (linesBody && !linesBody.querySelector("tr")) {
    addLine();
  }
  if (linesBody) {
    linesBody.addEventListener("input", (ev) => {
      const target = ev.target;
      if (!target || target.tagName !== "INPUT" || target.type !== "text") return;
      if (target.classList.contains("omd-item-code")) {
        updateItemLabel(target);
      } else if (target.classList.contains("omd-store-code")) {
        const tr = target.closest("tr");
        updateExpeditionInfoForRow(tr);
      }
    });
  }
  enforceDestinationRules();
  loadPrAddressForCurrentSelection();
});
