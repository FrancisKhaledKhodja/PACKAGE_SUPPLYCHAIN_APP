document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("form-stock-map");
  const codeInput = document.getElementById("code_article");
  const codeHelp = document.getElementById("code-article-help");
  const codeIgInput = document.getElementById("code_ig");
  const centerHelp = document.getElementById("center-help");
  const addressInput = document.getElementById("address");
  const searchHelp = document.getElementById("search-help");
  const horsTransitInput = document.getElementById("hors_transit");
  const statusDiv = document.getElementById("stock-map-status");
  const countDiv = document.getElementById("stock-map-count");
  const articleInfoDiv = document.getElementById("stock-map-article-info");
  const centerInfoDiv = document.getElementById("stock-map-center-info");
  const theadRow = document.getElementById("stock-map-thead-row");
  const tbodyRows = document.getElementById("stock-map-tbody-rows");
  const validateBtn = document.getElementById("btn-validate-selection");
  const summaryDiv = document.getElementById("stock-selection-summary");
  const stockMapPanel = document.getElementById("stock-map-panel");
  const stockMapToggleBtn = document.getElementById("stock-map-toggle");

  // Éléments OL (copiés depuis ol_mode_degrade.js)
  const techSelect = document.getElementById("omd-tech-select");
  const codeMagasinEl = document.getElementById("omd-code-magasin");
  const libelleMagasinEl = document.getElementById("omd-libelle-magasin");
  const codeTiersEl = document.getElementById("omd-code-tiers");
  const telephoneEl = document.getElementById("omd-telephone");
  const emailEl = document.getElementById("omd-email");
  const adresseEl = document.getElementById("omd-adresse");

  const typeCommandeSelect = document.getElementById("omd-type-commande");

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
  const btInput = document.getElementById("omd-bt");
  const dateBesoinInput = document.getElementById("omd-date-besoin");
  const commentaireInput = document.getElementById("omd-commentaire");
  const olStatusDiv = document.getElementById("omd-v2-status");
  const destSummaryDiv = document.getElementById("omd-dest-summary");

  if (!form) return;

  let map = null;
  let storesLayer = null;
  let refLayer = null;
  let currentRows = [];
  let lastApiData = null;

  // État OL (copié de ol_mode_degrade.js, réduit au nécessaire)
  let technicians = [];
  let igByCode = {};
  let storeMap = {};
  let currentIgAddress = "";
  let currentPrAddress = "";
  let currentUserLogin = "";

  let stockPanelCollapsed = false;

  function collapseStockPanel() {
    if (!stockMapPanel) return;
    const panel = stockMapPanel;
    panel.style.maxHeight = panel.scrollHeight + "px";
    // Forcer un reflow pour que la transition prenne bien
    void panel.offsetHeight;
    panel.style.maxHeight = "0px";
    panel.style.opacity = "0";
    panel.style.transform = "scaleY(0.97)";
    stockPanelCollapsed = true;
    if (stockMapToggleBtn) {
      stockMapToggleBtn.textContent = "Déplier la carte et les stocks";
    }
  }

  // Découper grossièrement une adresse en { line1, cp, ville }
  function parseAddressForFreeFields(rawAddress) {
    const result = { line1: "", cp: "", ville: "" };
    if (!rawAddress) return result;
    const txt = String(rawAddress).trim();
    if (!txt) return result;

    // On sépare éventuellement sur les virgules : "ligne1, 75000 Paris"
    const parts = txt.split(",").map(p => p.trim()).filter(Boolean);
    let first = "";
    let last = "";
    if (parts.length >= 2) {
      first = parts.slice(0, -1).join(", ");
      last = parts[parts.length - 1];
    } else {
      first = txt;
      last = txt;
    }

    // Chercher un CP sur 5 chiffres dans la dernière partie
    const m = last.match(/(\d{5})\s+(.*)$/);
    if (m) {
      result.cp = m[1].trim();
      result.ville = m[2].trim();
      if (parts.length >= 2) {
        // Adresse du type "rue, 75000 Paris" : on garde la partie avant la virgule
        result.line1 = first || last;
      } else {
        // Adresse en un seul bloc "100 rue ..., 75000 Paris" ou "100 rue ... 75000 Paris"
        // => on enlève le CP + ville de la ligne 1
        const idx = txt.search(/(\d{5})\s+.*$/);
        result.line1 = idx > 0 ? txt.slice(0, idx).trim() : txt;
      }
    } else {
      // Pas de CP détecté : tout en ligne 1
      result.line1 = txt;
    }
    return result;
  }

  function expandStockPanel() {
    if (!stockMapPanel) return;
    const panel = stockMapPanel;
    panel.style.maxHeight = panel.scrollHeight + "px";
    panel.style.opacity = "1";
    panel.style.transform = "scaleY(1)";
    stockPanelCollapsed = false;
    if (stockMapToggleBtn) {
      stockMapToggleBtn.textContent = "Replier la carte et les stocks";
    }
  }

  function toggleStockPanel() {
    if (stockPanelCollapsed) {
      expandStockPanel();
    } else {
      collapseStockPanel();
    }
  }

  // Aides visibles en permanence : pas de fonctions de masquage

  function buildGoogleMapsDirectionsUrl(row, apiData) {
    if (!row) return null;

    const storeLat = row.latitude;
    const storeLon = row.longitude;
    const storeAddr = row.adresse || "";

    const centerLat = typeof apiData.center_lat === "number" ? apiData.center_lat : null;
    const centerLon = typeof apiData.center_lon === "number" ? apiData.center_lon : null;
    const centerLabel = apiData.center_label || "";

    const base = "https://www.google.com/maps/dir/?api=1";

    // Cas idéal : coordonnées pour l'origine et la destination
    if (centerLat != null && centerLon != null && storeLat != null && storeLon != null) {
      const origin = `${centerLat},${centerLon}`;
      const dest = `${storeLat},${storeLon}`;
      return `${base}&origin=${encodeURIComponent(origin)}&destination=${encodeURIComponent(dest)}&travelmode=driving`;
    }

    // Fallback : adresses textuelles si disponibles
    const originText = centerLabel || "";
    const destText = storeAddr || "";
    if (originText || destText) {
      return `${base}&origin=${encodeURIComponent(originText)}&destination=${encodeURIComponent(destText)}&travelmode=driving`;
    }

    return null;
  }

  if (stockMapToggleBtn) {
    stockMapToggleBtn.addEventListener("click", () => {
      toggleStockPanel();
    });
  }

  // Aides (Étape 1, 2, 3) : permanentes, aucun listener pour les masquer

  // --- Logique OL (techniciens / destination) ---

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
      updateDestinationSummary();
      return;
    }

    const idx = parseInt(techSelect?.value || "0", 10);
    const t = technicians[idx];
    if (!t) {
      currentPrAddress = "";
      if (destPrAddressEl) destPrAddressEl.textContent = "";
      updateDestinationSummary();
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
      updateDestinationSummary();
      return;
    }

    try {
      const res = await fetch(API(`/technicians/ol_pudo_address/${encodeURIComponent(codePr)}`), {
        method: "GET",
        credentials: "include",
      });
      if (!res.ok) {
        if (res.status === 403) {
          if (olStatusDiv) {
            olStatusDiv.textContent = "Accès OL mode dégradé interdit (non autorisé).";
          }
          if (validateBtn) validateBtn.disabled = true;
        }
        currentPrAddress = "";
        if (destPrAddressEl) destPrAddressEl.textContent = "";
        updateDestinationSummary();
        return;
      }
      const data = await res.json();
      const adr = data.adresse_postale || "";
      const ens = data.enseigne || "";
      currentPrAddress = adr;
      if (destPrAddressEl) {
        const idx2 = parseInt(techSelect?.value || "0", 10);
        const t2 = technicians[idx2];
        let choix2 = "principal";
        const prChoixEl2 = document.querySelector("input[name='omd-pr-choice']:checked");
        if (prChoixEl2 && prChoixEl2.value) {
          choix2 = prChoixEl2.value;
        }
        const codePr2 = t2
          ? (choix2 === "hors_normes" ? (t2.pr_hors_normes || t2.pr_hors_norme) : t2.pr_principal)
          : "";

        const baseAdr = ens ? `${ens} - ${adr}` : adr;
        destPrAddressEl.textContent = codePr2 ? `${codePr2} - ${baseAdr}` : baseAdr;
      }
      updateDestinationSummary();
    } catch (e) {
      currentPrAddress = "";
      if (destPrAddressEl) destPrAddressEl.textContent = "";
      updateDestinationSummary();
    }
  }

  async function loadStores() {
    try {
      const res = await fetch(API("/technicians/ol_stores"), {
        method: "GET",
        credentials: "include",
      });
      if (!res.ok) {
        if (res.status === 403) {
          if (olStatusDiv) {
            olStatusDiv.textContent = "Accès OL mode dégradé interdit (non autorisé).";
          }
          if (validateBtn) validateBtn.disabled = true;
        }
        return;
      }
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
      if (destSummaryDiv) destSummaryDiv.textContent = "";
      return;
    }
    const ig = igByCode[code];
    if (!ig) {
      currentIgAddress = "";
      if (codeIgAddressEl) codeIgAddressEl.textContent = "";
      if (destSummaryDiv) destSummaryDiv.textContent = "";
      return;
    }
    currentIgAddress = ig.adresse_postale || "";
    if (codeIgAddressEl) {
      const lbl = ig.libelle_long_ig || "";
      const adr = ig.adresse_postale || "";
      codeIgAddressEl.textContent = lbl ? `${lbl} - ${adr}` : adr;
    }
    if (destSummaryDiv) {
      destSummaryDiv.textContent = currentIgAddress;
    }
  }

  function enforceDestinationRules() {
    const typeCmd = typeCommandeSelect ? (typeCommandeSelect.value || "").toUpperCase() : "";
    const isUrgent = typeCmd === "URGENT";
    const isMad = typeCmd === "MAD";
    const isStandard = typeCmd === "STANDARD";

    if (destTypeRadios && destTypeRadios.length > 0) {
      Array.from(destTypeRadios).forEach((r) => {
        const label = r.closest("label");

        if (isMad) {
          r.disabled = true;
          if (label) {
            label.style.opacity = "0.5";
            label.style.cursor = "not-allowed";
          }
          return;
        }

        if (isStandard) {
          const allow = r.value === "point_relais";
          r.disabled = !allow;
          if (label) {
            label.style.opacity = allow ? "1" : "0.5";
            label.style.cursor = allow ? "pointer" : "not-allowed";
          }
          return;
        }

        // Cas URGENT ou autre : radios actives par défaut ici;
        r.disabled = false;
        if (label) {
          label.style.opacity = "1";
          label.style.cursor = "pointer";
        }
      });
    }

    if (isMad && destTypeRadios && destTypeRadios.length > 0) {
      const codeIgRadio = Array.from(destTypeRadios).find(r => r.value === "code_ig");
      if (codeIgRadio) {
        codeIgRadio.checked = true;
      }
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

    if (isStandard && destTypeRadios && destTypeRadios.length > 0) {
      const prRadio = Array.from(destTypeRadios).find(r => r.value === "point_relais");
      if (prRadio) {
        prRadio.checked = true;
      }
    }

    if (isUrgent) {
      const prRadio = Array.from(destTypeRadios || []).find(r => r.value === "point_relais");
      if (prRadio) {
        prRadio.disabled = true;
        const prLabel = prRadio.closest("label");
        if (prLabel) {
          prLabel.style.opacity = "0.5";
        }
        if (prRadio.checked) {
          const codeIgRadio = Array.from(destTypeRadios).find(r => r.value === "code_ig");
          if (codeIgRadio) {
            codeIgRadio.checked = true;
          }
        }
      }
    }

    updateDestinationVisibility();
  }

  function enforceCenterInputsRules() {
    const typeCmd = typeCommandeSelect ? (typeCommandeSelect.value || "").toUpperCase() : "";
    const disableCenter = typeCmd === "STANDARD" || typeCmd === "MAD";

    if (codeIgInput) {
      codeIgInput.disabled = disableCenter;
      if (disableCenter) {
        codeIgInput.value = "";
      }
    }

    if (addressInput) {
      addressInput.disabled = disableCenter;
      if (disableCenter) {
        addressInput.value = "";
      }
    }
  }

  if (typeCommandeSelect) {
    typeCommandeSelect.addEventListener("change", () => {
      enforceDestinationRules();
      enforceCenterInputsRules();
    });
  }

  // Appliquer les règles initiales dès le chargement
  enforceDestinationRules();
  enforceCenterInputsRules();

  function buildDestinationSummaryText() {
    let dest = {};
    if (technicians.length && techSelect) {
      const idx = parseInt(techSelect.value || "0", 10);
      const t = technicians[idx];
      if (t) {
        dest = getDestination(t) || {};
      }
    }
    const typeCmd = typeCommandeSelect ? (typeCommandeSelect.value || "").toUpperCase() : "";

    // En mode MAD, on affiche simplement une mention générique
    if (typeCmd === "MAD") {
      return "Adresse de livraison = magasin(s) expéditeur(s)";
    }

    const dType = dest.type || "";
    if (dType === "code_ig" || dType === "point_relais") {
      return String(dest.adresse || "").trim();
    }
    if (dType === "adresse_libre") {
      const parts = [
        dest.raison_sociale || "",
        dest.adresse_ligne1 || "",
        dest.adresse_ligne2 || "",
        [dest.code_postal || "", dest.ville || ""].join(" ").trim(),
      ].map(x => String(x || "").trim()).filter(Boolean);
      return parts.join(" – ");
    }
    return "";
  }

  function updateDestinationSummary() {
    if (!destSummaryDiv) return;
    destSummaryDiv.textContent = buildDestinationSummaryText();
  }

  function renderTechnicians() {
    if (!techSelect) return;
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
      const res = await fetch(API(`/technicians/ol_igs_search?q=${encodeURIComponent(q)}&limit=50`), {
        method: "GET",
        credentials: "include",
      });
      if (!res.ok) {
        if (res.status === 403) {
          if (olStatusDiv) {
            olStatusDiv.textContent = "Accès OL mode dégradé interdit (non autorisé).";
          }
        }
        return;
      }
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
      const res = await fetch(API("/technicians/ol_technicians"), {
        method: "GET",
        credentials: "include",
      });
      if (!res.ok) {
        if (res.status === 403) {
          if (olStatusDiv) {
            olStatusDiv.textContent = "Accès OL mode dégradé interdit (non autorisé).";
          }
          if (validateBtn) validateBtn.disabled = true;
        }
        return;
      }
      const data = await res.json();
      technicians = data.technicians || [];
      renderTechnicians();
    } catch (e) {
      // ignore
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

  function updateTechnicianDetails() {
    if (!techSelect) return;
    const idx = parseInt(techSelect.value || "0", 10);
    const t = technicians[idx];
    if (!t) return;
    if (codeMagasinEl) codeMagasinEl.textContent = t.code_magasin || "";
    if (libelleMagasinEl) libelleMagasinEl.textContent = t.libelle_magasin || "";
    let techCodeTiers = t.code_tiers_daher || "";
    if (!techCodeTiers && t.code_magasin && storeMap[t.code_magasin]) {
      techCodeTiers = storeMap[t.code_magasin].code_tiers_daher || "";
    }
    if (codeTiersEl) codeTiersEl.textContent = techCodeTiers;
    if (telephoneEl) telephoneEl.textContent = t.telephone || "";
    if (emailEl) emailEl.textContent = t.email || "";
    if (adresseEl) adresseEl.textContent = t.adresse || "";

    loadPrAddressForCurrentSelection();
  }

  function ensureMap(lat, lon, zoom) {
    if (!window.L) return;
    if (!map) {
      map = L.map("stock-map").setView([lat, lon], zoom);
      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
        attribution: "&copy; OpenStreetMap contributors",
      }).addTo(map);
      storesLayer = L.layerGroup().addTo(map);
      refLayer = L.layerGroup().addTo(map);
    } else {
      map.setView([lat, lon], zoom);
      if (storesLayer) storesLayer.clearLayers();
      if (refLayer) refLayer.clearLayers();
    }
  }

  function fitMapToMarkers(rows) {
    if (!map || !window.L || !rows.length) return;
    const bounds = [];
    for (const r of rows) {
      const lat = r.latitude;
      const lon = r.longitude;
      if (lat != null && lon != null) {
        bounds.push([lat, lon]);
      }
    }
    if (!bounds.length) return;
    const latLngBounds = L.latLngBounds(bounds);
    map.fitBounds(latLngBounds.pad(0.1));
  }

  form.addEventListener("submit", async () => {
    const rawCode = (codeInput.value || "").trim();
    const typeCmd = typeCommandeSelect ? (typeCommandeSelect.value || "").toUpperCase() : "";
    let codeIg = (codeIgInput ? codeIgInput.value : "").trim();
    let address = (addressInput ? addressInput.value : "").trim();

    // En STANDARD et MAD, on ne considère pas le centre défini par code IG/adresse pour la carte
    if (typeCmd === "STANDARD" || typeCmd === "MAD") {
      codeIg = "";
      address = "";
    }
    if (!rawCode) {
      statusDiv.textContent = "Merci de saisir un code article.";
      return;
    }

    statusDiv.textContent = "Chargement des magasins en stock...";
    countDiv.textContent = "";
    articleInfoDiv.textContent = "";
    if (centerInfoDiv) centerInfoDiv.textContent = "";
    theadRow.innerHTML = "";
    tbodyRows.innerHTML = "";
    currentRows = [];
    if (storesLayer) storesLayer.clearLayers();
    if (refLayer) refLayer.clearLayers();

    try {
      const typeDepotValues = Array.from(document.querySelectorAll("input[name='type_de_depot']:checked")).map(cb => cb.value);
      const codeQualiteValues = Array.from(document.querySelectorAll("input[name='code_qualite']:checked")).map(cb => cb.value);
      const flagStockValues = Array.from(document.querySelectorAll("input[name='flag_stock_d_m']:checked")).map(cb => cb.value);
      const horsTransitOnly = horsTransitInput ? !!horsTransitInput.checked : false;

      // Gestion de plusieurs codes article séparés par des ";"
      const codes = rawCode
        .split(";")
        .map((c) => (c || "").trim().toUpperCase())
        .filter((c) => !!c);

      if (!codes.length) {
        statusDiv.textContent = "Merci de saisir au moins un code article valide.";
        return;
      }

      let allRows = [];
      let firstApiData = null;

      for (let i = 0; i < codes.length; i += 1) {
        const code = codes[i];
        // Pour permettre au backend de calculer les distances magasin ↔ PR du technicien
        let pr_principal = undefined;
        let pr_hors_normes = undefined;
        if (typeCmd === "STANDARD" && technicians.length && techSelect) {
          const idx = parseInt(techSelect.value || "0", 10);
          const t = technicians[idx];
          if (t) {
            pr_principal = t.pr_principal || undefined;
            pr_hors_normes = t.pr_hors_normes || t.pr_hors_norme || undefined;
          }
        }

        const resp = await fetch(API("/stores/stock-map"), {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({
            code_article: code,
            code_ig: codeIg || undefined,
            address: address || undefined,
            pr_principal,
            pr_hors_normes,
            type_de_depot: typeDepotValues,
            code_qualite: codeQualiteValues,
            flag_stock_d_m: flagStockValues,
            hors_transit_only: horsTransitOnly,
          }),
        });

        if (!resp.ok) {
          statusDiv.textContent = `Erreur API (${resp.status}) pour le code article ${code}`;
          return;
        }

        const dataPart = await resp.json();
        const rowsPart = dataPart.rows || [];

        // S'assurer que chaque ligne porte bien le code article concerné
        rowsPart.forEach((r) => {
          if (!r.code_article) {
            r.code_article = code;
          }
        });

        if (!firstApiData) {
          firstApiData = { data: dataPart, code };
        }

        allRows = allRows.concat(rowsPart);
      }

      const data = firstApiData ? firstApiData.data : { rows: allRows };
      const rows = allRows;
      currentRows = rows;
      lastApiData = data;

      if (!rows.length) {
        statusDiv.textContent = "Aucun magasin avec ces codes article en stock (selon les filtres qualité/stock/type de dépôt).";
        countDiv.textContent = "0 magasin";
        return;
      }

      const storeArticles = {};
      rows.forEach((r) => {
        const storeCode = String(r.code_magasin || "");
        const artCode = String(r.code_article || "").toUpperCase();
        if (!storeCode || !artCode) return;
        if (!storeArticles[storeCode]) {
          storeArticles[storeCode] = new Set();
        }
        storeArticles[storeCode].add(artCode);
      });

      function storeHasAllArticles(storeCode) {
        const s = storeArticles[storeCode];
        if (!s) return false;
        return codes.every((c) => s.has(c));
      }

      rows.sort((a, b) => {
        const sa = String(a.code_magasin || "");
        const sb = String(b.code_magasin || "");

        // Cas STANDARD : conserver la logique existante (tri par tous les articles + distance PR principal)
        if (typeCmd === "STANDARD" && codes.length > 0) {
          // 1) Magasins ayant tous les articles d'abord
          const aAll = storeHasAllArticles(sa);
          const bAll = storeHasAllArticles(sb);
          if (aAll !== bAll) {
            return aAll ? -1 : 1;
          }

          // 2) Puis par distance au PR principal (croissante, null en dernier)
          const daPr = typeof a.distance_pr_principal_km === "number" ? a.distance_pr_principal_km : null;
          const dbPr = typeof b.distance_pr_principal_km === "number" ? b.distance_pr_principal_km : null;
          if (daPr == null && dbPr == null) {
            // 3) Si égalité (ou pas de distance), tri par code magasin (ordre alphabétique)
            if (sa !== sb) {
              return sa.localeCompare(sb, "fr", { sensitivity: "base" });
            }
            return 0;
          }
          if (daPr == null) return 1;
          if (dbPr == null) return -1;
          const cmpPr = daPr - dbPr;
          if (cmpPr !== 0) return cmpPr;

          // 3 bis) À distance PR égale, tri par code magasin
          if (sa !== sb) {
            return sa.localeCompare(sb, "fr", { sensitivity: "base" });
          }
          return 0;
        }

        // Cas URGENT et MAD :
        // 1) Tous les articles en stock (true) d'abord
        // 2) Puis distance_km croissante (null en dernier)
        // 3) Puis code_magasin croissant
        if ((typeCmd === "URGENT" || typeCmd === "MAD") && codes.length > 0) {
          const aAll = storeHasAllArticles(sa);
          const bAll = storeHasAllArticles(sb);
          if (aAll !== bAll) {
            return aAll ? -1 : 1; // true avant false
          }

          const da = typeof a.distance_km === "number" ? a.distance_km : null;
          const db = typeof b.distance_km === "number" ? b.distance_km : null;
          if (da == null && db == null) {
            if (sa !== sb) {
              return sa.localeCompare(sb, "fr", { sensitivity: "base" });
            }
            return 0;
          }
          if (da == null) return 1;
          if (db == null) return -1;
          const cmp = da - db;
          if (cmp !== 0) return cmp;

          if (sa !== sb) {
            return sa.localeCompare(sb, "fr", { sensitivity: "base" });
          }
          return 0;
        }

        // Autres modes : tri historique par distance_km croissante (null en dernier)
        const da = typeof a.distance_km === "number" ? a.distance_km : null;
        const db = typeof b.distance_km === "number" ? b.distance_km : null;
        if (da == null && db == null) return 0;
        if (da == null) return 1;
        if (db == null) return -1;
        return da - db;
      });

      const first = rows[0];
      if (codes.length === 1) {
        const codeArticle = first.code_article || codes[0];
        const libelle = first.libelle_court_article || "";
        articleInfoDiv.textContent = libelle
          ? `${codeArticle} - ${libelle}`
          : codeArticle;
      } else {
        // Afficher simplement la liste des codes saisis
        articleInfoDiv.textContent = codes.join(" ; ");
      }

      countDiv.textContent = `${rows.length} magasin(s) avec du stock`;

      if (data.center_label || data.center_lat != null) {
        const parts = [];
        if (data.center_label) parts.push(data.center_label);
        if (typeof data.center_lat === "number" && typeof data.center_lon === "number") {
          parts.push(`(${data.center_lat.toFixed(4)}, ${data.center_lon.toFixed(4)})`);
        }
        if (centerInfoDiv && parts.length) {
          centerInfoDiv.textContent = "Centre : " + parts.join(" ");
        }
      }

      // Colonnes affichées dans le tableau, en commençant par le code article et la quantité totale en stock
      const baseColumns = [
        "code_article",
        "code_magasin",
        "libelle_magasin",
        "type_de_depot",
        "code_qualite",
        "flag_stock_d_m",
        "qte_stock_total",
        "has_all_articles",
        "distance_km",
        "adresse",
      ];

      const columns = baseColumns.filter((c) =>
        c === "has_all_articles"
          ? true // toujours afficher la colonne "Tous les articles en stock"
          : Object.prototype.hasOwnProperty.call(first, c)
      );

      // En mode STANDARD, ajouter les distances vers les PR du technicien si présentes
      if (typeCmd === "STANDARD") {
        if (Object.prototype.hasOwnProperty.call(first, "distance_pr_principal_km")) {
          columns.push("distance_pr_principal_km");
        }
        if (Object.prototype.hasOwnProperty.call(first, "distance_pr_hors_normes_km")) {
          columns.push("distance_pr_hors_normes_km");
        }
      }

      const columnLabels = {
        code_article: "Code article",
        code_magasin: "Code magasin",
        libelle_magasin: "Libellé magasin",
        type_de_depot: "Type de dépôt",
        code_qualite: "Code qualité",
        flag_stock_d_m: "Type stock (M/D)",
        qte_stock_total: "Qté stock totale",
        has_all_articles: "Tous les articles en stock",
        distance_km: "Distance centre (km)",
        adresse: "Adresse magasin",
        distance_pr_principal_km: "Dist. PR principal (km)",
        distance_pr_hors_normes_km: "Dist. PR hors normes (km)",
      };

      theadRow.innerHTML = "";
      // Colonne de sélection
      const thSelect = document.createElement("th");
      thSelect.textContent = "Sélection";
      theadRow.appendChild(thSelect);
      for (const col of columns) {
        const th = document.createElement("th");
        th.textContent = columnLabels[col] || col;
        theadRow.appendChild(th);
      }
      // Colonne supplémentaire pour l'itinéraire Google Maps
      const thDir = document.createElement("th");
      thDir.textContent = "Itinéraire";
      theadRow.appendChild(thDir);

      tbodyRows.innerHTML = "";
      rows.forEach((row, idx) => {
        const tr = document.createElement("tr");

        // Cellule sélection (checkbox)
        const tdSelect = document.createElement("td");
        const cb = document.createElement("input");
        cb.type = "checkbox";
        cb.className = "stock-select";
        cb.dataset.rowIndex = String(idx);
        tdSelect.appendChild(cb);
        tr.appendChild(tdSelect);
        for (const col of columns) {
          const td = document.createElement("td");
          let val = row[col];

          if (col === "has_all_articles") {
            const storeCode = String(row.code_magasin || "");
            const all = storeCode ? storeHasAllArticles(storeCode) : false;
            td.textContent = all ? "Oui" : "Non";
          } else if (col === "code_article") {
            const codeVal = val != null ? String(val) : "";
            if (codeVal) {
              const a = document.createElement("a");
              a.href = `stock.html?code=${encodeURIComponent(codeVal)}`;
              a.target = "_blank";
              a.rel = "noopener noreferrer";
              a.textContent = codeVal;
              td.appendChild(a);
            } else {
              td.textContent = "";
            }
          } else if (col === "qte_stock_total" && typeof val === "number") {
            td.textContent = val.toFixed(2);
          } else if ((col === "distance_km" || col === "distance_pr_principal_km" || col === "distance_pr_hors_normes_km") && typeof val === "number") {
            td.textContent = val.toFixed(1);
          } else {
            td.textContent = val != null ? String(val) : "";
          }

          tr.appendChild(td);
        }

        // Cellule lien itinéraire Google Maps
        const tdDir = document.createElement("td");
        const gmapsUrl = buildGoogleMapsDirectionsUrl(row, data);
        if (gmapsUrl) {
          const a = document.createElement("a");
          a.href = gmapsUrl;
          a.target = "_blank";
          a.rel = "noopener noreferrer";
          a.textContent = "Itinéraire";
          tdDir.appendChild(a);
        }
        tr.appendChild(tdDir);

        tbodyRows.appendChild(tr);
      });

      const withCoords = rows.filter(r => r.latitude != null && r.longitude != null);
      if (withCoords.length) {
        // Centre prioritaire : center_lat/center_lon si fournis par l'API, sinon premier magasin
        const centerLat = typeof data.center_lat === "number" ? data.center_lat : withCoords[0].latitude;
        const centerLon = typeof data.center_lon === "number" ? data.center_lon : withCoords[0].longitude;
        ensureMap(centerLat, centerLon, 6);

        if (refLayer) {
          if (typeof data.center_lat === "number" && typeof data.center_lon === "number") {
            const refMarker = L.circleMarker([data.center_lat, data.center_lon], {
              radius: 7,
              color: "#f97316",
              fillColor: "#fdba74",
              fillOpacity: 0.9,
            });
            const label = data.center_label || "Point de référence";
            refMarker.bindPopup(label);
            refMarker.addTo(refLayer);
          }

          // En mode STANDARD, afficher aussi les PR principal / hors normes du technicien si disponibles
          if (typeCmd === "STANDARD") {
            if (typeof data.pr_principal_lat === "number" && typeof data.pr_principal_lon === "number") {
              const prMainMarker = L.circleMarker([data.pr_principal_lat, data.pr_principal_lon], {
                radius: 6,
                color: "#22c55e",
                fillColor: "#bbf7d0",
                fillOpacity: 0.9,
              });
              const labelMain = data.pr_principal_label || "Point relais principal du technicien";
              prMainMarker.bindPopup(labelMain);
              prMainMarker.addTo(refLayer);
            }

            if (typeof data.pr_hn_lat === "number" && typeof data.pr_hn_lon === "number") {
              const prHnMarker = L.circleMarker([data.pr_hn_lat, data.pr_hn_lon], {
                radius: 6,
                color: "#6366f1",
                fillColor: "#c7d2fe",
                fillOpacity: 0.9,
              });
              const labelHn = data.pr_hn_label || "Point relais hors normes du technicien";
              prHnMarker.bindPopup(labelHn);
              prHnMarker.addTo(refLayer);
            }
          }
        }

        // Regrouper par magasin (et coordonnées) pour avoir un seul marker par magasin
        const groups = new Map();
        for (const r of withCoords) {
          const lat = r.latitude;
          const lon = r.longitude;
          if (lat == null || lon == null) continue;
          const key = `${r.code_magasin || ""}||${lat}||${lon}`;
          let g = groups.get(key);
          if (!g) {
            g = {
              lat,
              lon,
              code_magasin: r.code_magasin || "",
              libelle_magasin: r.libelle_magasin || "",
              adresse1: r.adresse1 || "",
              adresse2: r.adresse2 || "",
              code_postal: r.code_postal || "",
              ville: r.ville || "",
              distance_km: typeof r.distance_km === "number" ? r.distance_km : null,
              articles: [],
            };
            groups.set(key, g);
          }
          // Mettre à jour l adresse si une ligne suivante apporte plus d information
          g.adresse1 = g.adresse1 || r.adresse1 || "";
          g.adresse2 = g.adresse2 || r.adresse2 || "";
          g.code_postal = g.code_postal || r.code_postal || "";
          g.ville = g.ville || r.ville || "";

          g.articles.push({
            code_article: r.code_article || "",
            qte_stock_total: r.qte_stock_total,
          });
        }

        for (const g of groups.values()) {
          if (!storesLayer || !window.L) continue;

          const hasAllArticles = codes.length > 0 && codes.every((code) =>
            g.articles.some((a) => (a.code_article || "").toUpperCase() === code)
          );

          const markerIcon = hasAllArticles
            ? L.icon({
                iconUrl: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png",
                shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
                iconSize: [25, 41],
                iconAnchor: [12, 41],
                shadowSize: [41, 41],
              })
            : L.icon({
                iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
                shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
                iconSize: [25, 41],
                iconAnchor: [12, 41],
                shadowSize: [41, 41],
              });

          const marker = L.marker([g.lat, g.lon], {
            icon: markerIcon,
          });

          const lines = [];
          // 1) Première ligne : code + libellé magasin
          const magasinLabel = `${g.code_magasin || ""} - ${g.libelle_magasin || ""}`.trim();
          if (magasinLabel) {
            lines.push(magasinLabel);
          }

          // 2) Deuxième ligne : adresse détaillée (adresse1, adresse2, code_postal, ville)
          const addrParts = [];
          if (g.adresse1) addrParts.push(String(g.adresse1));
          if (g.adresse2) addrParts.push(String(g.adresse2));
          if (g.code_postal) addrParts.push(String(g.code_postal));
          if (g.ville) addrParts.push(String(g.ville));
          if (addrParts.length) {
            lines.push(addrParts.join(" "));
          }

          // 3) Troisième ligne : distance (si disponible)
          if (g.distance_km != null) {
            lines.push(`${g.distance_km.toFixed(1)} km`);
          }

          // 4) Puis une ligne par code article avec la quantité
          g.articles.forEach(a => {
            if (!a.code_article && a.qte_stock_total == null) return;
            const stockTxt = typeof a.qte_stock_total === "number" ? a.qte_stock_total.toFixed(2) : a.qte_stock_total;
            const articleLineParts = [];
            if (a.code_article) articleLineParts.push(`Article : ${a.code_article}`);
            if (stockTxt != null) articleLineParts.push(`Stock (selon filtres) : ${stockTxt}`);
            const articleLine = articleLineParts.join(" – ");
            if (articleLine) {
              lines.push(articleLine);
            }
          });

          marker.bindPopup(lines.join("<br>"));
          marker.addTo(storesLayer);
        }

        fitMapToMarkers(withCoords);
      } else {
        statusDiv.textContent = "Des magasins ont du stock mais aucune coordonnée géographique n'est disponible pour les afficher sur la carte.";
      }

      statusDiv.textContent = "";
    } catch (e) {
      statusDiv.textContent = "Erreur de communication avec l'API.";
    }
  });

  // Construit les lignes à partir du récapitulatif (après clic sur "Valider la sélection")
  function getSelectedLinesForPayload() {
    const rows = [];
    if (!summaryDiv) return rows;
    const trEls = summaryDiv.querySelectorAll("tbody tr");
    trEls.forEach((tr) => {
      const idx = parseInt(tr.dataset.rowIndex || "-1", 10);
      const hasIndex = !Number.isNaN(idx) && currentRows[idx];
      let base = null;
      let codeArticle = "";
      let libelle = "";
      let codeMagasin = "";

      if (hasIndex) {
        base = currentRows[idx];
        codeArticle = base.code_article || "";
        libelle = base.libelle_court_article || "";
        codeMagasin = base.code_magasin || "";
      } else {
        const manualCodeInput = tr.querySelector("input[data-field='code_article']");
        const manualLibInput = tr.querySelector("input[data-field='libelle']");
        const manualMagEl = tr.querySelector("[data-field='code_magasin']");
        codeArticle = manualCodeInput ? String(manualCodeInput.value || "").trim().toUpperCase() : "";
        libelle = manualLibInput ? String(manualLibInput.value || "").trim() : "";
        codeMagasin = manualMagEl ? String(manualMagEl.value || "").trim().toUpperCase() : "";
      }

      if (!codeArticle) {
        return;
      }

      const qtyInput = tr.querySelector("input[data-field='quantite']") || tr.querySelector("input[type='number']");
      const q = qtyInput ? Number(qtyInput.value || "0") : 0;

      rows.push({
        code_article: codeArticle,
        libelle: libelle,
        quantite: q,
        code_magasin: codeMagasin,
        hors_norme: false,
      });
    });
    return rows;
  }

  // Récupération des infos article (libellé + flag hors_norme) via les mêmes APIs que la V1
  async function fetchItemInfo(code) {
    const norm = (code || "").trim().toUpperCase();
    if (!norm) return { hors_norme: false, libelle: "" };

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

    // 1) Tentative via /items/{code}/details
    try {
      const res = await fetch(API(`/items/${encodeURIComponent(norm)}/details`));
      if (res.ok) {
        const data = await res.json();
        const item = data && data.item ? data.item : {};
        const flagHn = isOui(item.article_hors_norme) || isOui(item.article_hors_normes);
        const flagFragile = isY(item.fragile);
        const flagAffr = isY(item.affretement);
        const libelle = item.libelle_court_article || item.libelle_article || "";
        if (flagHn || flagFragile || flagAffr) {
          return { hors_norme: true, libelle };
        }
        if (libelle) {
          return { hors_norme: false, libelle };
        }
      }
    } catch (e) {
      // ignore et on tente la recherche globale
    }

    // 2) Fallback via /items/search
    try {
      const resSearch = await fetch(API("/items/search"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ q: norm, filters: {}, limit: 1 }),
      });
      if (resSearch.ok) {
        const searchData = await resSearch.json();
        const rows = searchData.rows || [];
        if (rows.length > 0) {
          const row = rows[0] || {};
          const flagHn =
            isOui(row.article_hors_norme) ||
            isOui(row.article_hors_normes) ||
            isOui(row.article_hors_normes_right);
          const flagFragile = isY(row.fragile);
          const flagAffr = isY(row.affretement);
          const libelle = row.libelle_court_article || row.libelle_article || "";
          if (flagHn || flagFragile || flagAffr) {
            return { hors_norme: true, libelle };
          }
          if (libelle) {
            return { hors_norme: false, libelle };
          }
        }
      }
    } catch (e) {
      // ignore, on considérera non hors norme
    }

    return { hors_norme: false, libelle: "" };
  }

  // Détermination du flag hors_norme pour une ligne article (logique V1)
  async function computeHorsNormeForCode(code) {
    const info = await fetchItemInfo(code);
    return !!info.hors_norme;
  }

  async function enrichLinesWithHorsNorme(lines) {
    if (!Array.isArray(lines) || !lines.length) return lines;
    const cache = {};
    for (const l of lines) {
      const code = (l.code_article || "").trim().toUpperCase();
      if (!code) {
        l.hors_norme = false;
        continue;
      }
      if (!(code in cache)) {
        cache[code] = await computeHorsNormeForCode(code);
      }
      l.hors_norme = !!cache[code];
    }
    return lines;
  }

  function getDestination(t) {
    const destTypeEl = document.querySelector("input[name='omd-destination-type']:checked");
    const destType = destTypeEl ? destTypeEl.value : "code_ig";

    if (destType === "code_ig") {
      const codeIg = codeIgSelect ? (codeIgSelect.value || "").trim() : "";
      return {
        type: "code_ig",
        code_ig: codeIg,
        adresse: currentIgAddress,
      };
    }

    if (destType === "point_relais") {
      let choix = "principal";
      const prChoixEl = document.querySelector("input[name='omd-pr-choice']:checked");
      if (prChoixEl && prChoixEl.value) {
        choix = prChoixEl.value;
      }
      const codePr = choix === "hors_normes" ? (t.pr_hors_normes || t.pr_hors_norme) : t.pr_principal;
      return {
        type: "point_relais",
        choix: choix,
        code_pr: codePr || "",
        adresse: currentPrAddress,
      };
    }

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
      ville: ville,
    };
  }

  function buildPayloadFromSelection() {
    if (!olStatusDiv) {
      // on utilise éventuellement stock-map-status si besoin
    }
    if (olStatusDiv) olStatusDiv.textContent = "";

    const bt = (btInput?.value || "").trim();
    const dateBesoinRaw = dateBesoinInput && dateBesoinInput.value ? dateBesoinInput.value : "";
    const commentaireLibre = (commentaireInput && commentaireInput.value) ? commentaireInput.value.trim() : "";
    const typeCommande = typeCommandeSelect ? typeCommandeSelect.value : "";

    const idx = parseInt(techSelect?.value || "0", 10);
    const t = technicians[idx];

    const lines = getSelectedLinesForPayload();
    const nonEmptyLines = lines.filter(l => (l.code_article || "").trim() !== "");

    const setError = (msg) => {
      if (olStatusDiv) olStatusDiv.textContent = msg;
      else if (statusDiv) statusDiv.textContent = msg;
    };

    if (!bt) {
      setError("Merci de saisir un numéro de BT.");
      return null;
    }
    if (!t) {
      setError("Merci de sélectionner un technicien.");
      return null;
    }
    if (nonEmptyLines.length === 0) {
      setError("Merci de sélectionner au moins une ligne de stock et de saisir une quantité.");
      return null;
    }

    const missingStore = nonEmptyLines.find(l => !(l.code_magasin || "").trim());
    if (missingStore) {
      setError("Merci de renseigner un code magasin expéditeur pour chaque ligne sélectionnée.");
      return null;
    }

    const destination = getDestination(t);

    if (destination.type === "code_ig") {
      const codeIg = (destination.code_ig || "").trim();
      if (!codeIg) {
        setError("Merci de renseigner un code IG pour l'adresse de livraison.");
        return null;
      }
    } else if (destination.type === "adresse_libre") {
      if (!destination.adresse_ligne1 || !destination.code_postal || !destination.ville) {
        setError("Merci de compléter l'adresse libre (adresse, code postal, ville).");
        return null;
      }
    }

    return {
      bt: bt,
      type_commande: typeCommande,
      date_besoin: dateBesoinRaw,
      commentaire_libre: commentaireLibre,
      technicien: t,
      destination: destination,
      lignes: nonEmptyLines,
    };
  }

  function buildEmailBodyFromPayload(payload) {
    const now = new Date();
    const pad = (n) => String(n).padStart(2, "0");
    const dateStr = `${pad(now.getDate())}/${pad(now.getMonth() + 1)}/${now.getFullYear()} ${pad(now.getHours())}:${pad(now.getMinutes())}`;

    const login = currentUserLogin || "";

    const dest = payload.destination || {};
    const tech = payload.technicien || {};
    const dateBesoinRaw = payload.date_besoin || "";
    const commentaireLibre = payload.commentaire_libre || "";

    let dateBesoinText = "";
    if (dateBesoinRaw) {
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

    if ((payload.type_commande || "").toUpperCase() === "MAD") {
      destText = expText || "(adresse de livraison = magasin(s) expéditeur(s))";
    }

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

    let techCodeMag = tech.code_magasin || "";
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

    if (googleMapsUrl) {
      bodyLines.push("");
      bodyLines.push("LIEN GOOGLE MAP :");
      bodyLines.push(googleMapsUrl);
    }

    return bodyLines.join("\n");
  }

  function sendMailFromPayload(payload) {
    const lignes = payload.lignes || [];
    const hasLines = lignes.length > 0;
    const allMplc = hasLines && lignes.every(l => (l.code_magasin || "").trim().toUpperCase() === "MPLC");
    const anyMplc = hasLines && lignes.some(l => (l.code_magasin || "").trim().toUpperCase() === "MPLC");

    const lignesMplc = lignes.filter(l => (l.code_magasin || "").trim().toUpperCase() === "MPLC");
    const lignesAutres = lignes.filter(l => (l.code_magasin || "").trim().toUpperCase() !== "MPLC");

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

    function openMailForLines(linesSubset, mode) {
      const subPayload = { ...payload, lignes: linesSubset };
      const body = encodeURIComponent(buildEmailBodyFromPayload(subPayload));

      const importance = "&X-Priority=1%20(Highest)&Importance=High";

      if (mode === "mplc") {
        const subject = buildSubject("DAHER");
        const to = encodeURIComponent("ordotdf@daher.com; t.robas@daher.com");
        const cc = encodeURIComponent("logistique_pilotage_operationnel@tdf.fr; sophie.khayat@tdf.fr; francis.khaled-khodja@tdf.fr; adeline.gillet@tdf.fr");
        const mailto = `mailto:${to}?cc=${cc}&subject=${subject}&body=${body}${importance}`;
        window.location.href = mailto;
      } else if (mode === "lm2s") {
        const subject = buildSubject("LM2S");
        const to = encodeURIComponent("serviceclients@lm2s.fr");
        const cc = encodeURIComponent("logistique_pilotage_operationnel@tdf.fr; sophie.khayat@tdf.fr; francis.khaled-khodja@tdf.fr; adeline.gillet@tdf.fr");
        const mailto = `mailto:${to}?cc=${cc}&subject=${subject}&body=${body}${importance}`;
        window.location.href = mailto;
      } else {
        const subject = buildSubject("");
        const mailto = `mailto:?subject=${subject}&body=${body}${importance}`;
        window.location.href = mailto;
      }
    }

    if (!hasLines) {
      const body = encodeURIComponent(buildEmailBodyFromPayload(payload));
      const subject = buildSubject("");
      const importance = "&X-Priority=1%20(Highest)&Importance=High";
      const mailto = `mailto:?subject=${subject}&body=${body}${importance}`;
      window.location.href = mailto;
      return;
    }

    if (allMplc) {
      openMailForLines(lignes, "mplc");
    } else if (hasLines && !anyMplc) {
      openMailForLines(lignes, "lm2s");
    } else {
      if (lignesMplc.length) {
        openMailForLines(lignesMplc, "mplc");
      }
      if (lignesAutres.length) {
        openMailForLines(lignesAutres, "lm2s");
      }
      if (olStatusDiv) {
        olStatusDiv.textContent = "Deux mails générés : Daher (lignes MPLC) et LM2S (autres lignes).";
      }
    }
  }

  // Initialisation logique OL
  updateDestinationVisibility();
  enforceDestinationRules();
  loadCurrentUserLogin();
  loadTechnicians();
  loadStores();
  updateDestinationSummary();

  // Écouteurs pour la destination
  Array.from(destTypeRadios || []).forEach((r) => {
    r.addEventListener("change", () => {
      updateDestinationVisibility();
      loadPrAddressForCurrentSelection();
      updateDestinationSummary();
    });
  });

  Array.from(prChoiceRadios || []).forEach((r) => {
    r.addEventListener("change", () => {
      loadPrAddressForCurrentSelection();
      updateDestinationSummary();
    });
  });

  if (typeCommandeSelect) {
    typeCommandeSelect.addEventListener("change", () => {
      enforceDestinationRules();
      updateDestinationSummary();
    });
  }

  if (codeIgSelect) {
    codeIgSelect.addEventListener("input", () => {
      debouncedSearchIgs(codeIgSelect.value || "");
      updateCodeIgAddress();
      updateDestinationSummary();
    });
    codeIgSelect.addEventListener("change", () => {
      updateCodeIgAddress();
      updateDestinationSummary();
    });
  }

  // Synchroniser le code IG saisi pour le centre de la carte avec le champ de destination OL
  if (codeIgInput && codeIgSelect) {
    const syncCenterCodeIgToDestination = async () => {
      const raw = (codeIgInput.value || "").trim();
      if (!raw) return;
      const norm = raw.toUpperCase();
      codeIgInput.value = norm;
      codeIgSelect.value = norm;

      await searchIgs(norm);
      updateCodeIgAddress();
      updateDestinationSummary();
    };

    codeIgInput.addEventListener("blur", () => {
      syncCenterCodeIgToDestination();
    });

    codeIgInput.addEventListener("change", () => {
      syncCenterCodeIgToDestination();
    });
  }

  // En mode URGENT, si une adresse est saisie pour le centre de la carte,
  // l'utiliser comme adresse de livraison en bas (adresse libre)
  if (addressInput && destTypeRadios && destFreeBlock && freeL1Input) {
    const syncUrgentAddressToFreeDestination = () => {
      const typeCmd = typeCommandeSelect ? (typeCommandeSelect.value || "").toUpperCase() : "";
      if (typeCmd !== "URGENT") return;

      const raw = (addressInput.value || "").trim();
      if (!raw) return;

      const parsed = parseAddressForFreeFields(raw);

      // Sélectionner le type de destination "adresse_libre"
      const freeRadio = Array.from(destTypeRadios).find(r => r.value === "adresse_libre");
      if (freeRadio) {
        freeRadio.disabled = false;
        freeRadio.checked = true;
      }

      // Afficher le bloc adresse libre et masquer les autres blocs de destination
      if (destCodeIgBlock) destCodeIgBlock.style.display = "none";
      if (destPrBlock) destPrBlock.style.display = "none";
      destFreeBlock.style.display = "block";

      // Pré-remplir au minimum la ligne 1 avec l'adresse saisie (en majuscules)
      // et mettre par défaut la raison sociale à "TDFRDV" si elle est vide
      if (freeRaisonInput && !freeRaisonInput.value) {
        freeRaisonInput.value = "TDFRDV";
      }
      const line1Upper = (parsed.line1 || raw).toUpperCase();
      freeL1Input.value = line1Upper;
      if (freeCpInput && parsed.cp) freeCpInput.value = String(parsed.cp).toUpperCase();
      if (freeVilleInput && parsed.ville) freeVilleInput.value = parsed.ville.toUpperCase();

      updateDestinationSummary();
    };

    addressInput.addEventListener("blur", () => {
      syncUrgentAddressToFreeDestination();
    });

    addressInput.addEventListener("change", () => {
      syncUrgentAddressToFreeDestination();
    });
  }

  if (techSelect) {
    techSelect.addEventListener("change", () => {
      updateTechnicianDetails();
      updateDestinationSummary();
    });
  }

  function addManualSummaryLine() {
    if (!summaryDiv) return;
    const tbody = summaryDiv.querySelector("tbody");
    if (!tbody) return;

    const tr = document.createElement("tr");
    tr.innerHTML =
      "<td><input type='text' data-field='code_article' style='width:8rem; background:#ffffff; color:#111827;' /></td>" +
      "<td><input type='text' data-field='libelle' style='width:100%; background:#ffffff; color:#111827;' /></td>" +
      "<td><input type='number' data-field='quantite' min='0' step='1' value='1' style='width:6rem; background:#ffffff; color:#111827;' /></td>" +
      "<td><select data-field='code_magasin' style='width:8rem; background:#ffffff; color:#111827;'></select></td>" +
      "<td>Non</td>" +
      "<td></td>" +
      "<td></td>" +
      "<td><button type='button' class='omd-remove-line' style='font-size:0.8rem;'>Supprimer</button></td>";

    tbody.appendChild(tr);

    const codeInput = tr.querySelector("input[data-field='code_article']");
    const libInput = tr.querySelector("input[data-field='libelle']");
    const storeSelect = tr.querySelector("select[data-field='code_magasin']");
    const horsNormeCell = tr.children[4] || null;
    const destCell = tr.children[5] || null;
    const itinCell = tr.children[6] || null;

    // Adresse de livraison : même texte que pour les lignes issues de la sélection
    const destSummaryText = String(buildDestinationSummaryText() || "").trim();
    if (destCell) {
      destCell.textContent = destSummaryText;
    }

    // Peupler la liste des magasins à partir de storeMap (déjà filtré NATIONAL/LOCAL, statut 0, code "M")
    if (storeSelect && storeMap) {
      storeSelect.innerHTML = "";
      const codes = Object.keys(storeMap).sort();
      const emptyOpt = document.createElement("option");
      emptyOpt.value = "";
      emptyOpt.textContent = "";
      storeSelect.appendChild(emptyOpt);
      codes.forEach((code) => {
        const s = storeMap[code] || {};
        const opt = document.createElement("option");
        opt.value = String(code || "").toUpperCase();
        const parts = [code];
        if (s.libelle_magasin) parts.push(s.libelle_magasin);
        if (s.adresse_postale) parts.push(s.adresse_postale);
        opt.textContent = parts.join(" - ");
        storeSelect.appendChild(opt);
      });

      // Mettre à jour le lien Google Maps à chaque changement de magasin sélectionné
      storeSelect.addEventListener("change", () => {
        if (!itinCell) return;
        itinCell.innerHTML = "";
        const codeMag = String(storeSelect.value || "").trim().toUpperCase();
        if (!codeMag || !storeMap[codeMag]) {
          return;
        }
        const store = storeMap[codeMag];
        const originAddr = (store.adresse_postale || "").trim() ||
          [store.adresse1 || "", store.adresse2 || "", store.code_postal || "", store.ville || ""]
            .map(x => String(x || "").trim())
            .filter(Boolean)
            .join(" ");

        let destAddr = "";
        const typeCmd = typeCommandeSelect ? (typeCommandeSelect.value || "").toUpperCase() : "";

        if (typeCmd === "MAD") {
          destAddr = originAddr;
        } else {
          const idxTech = parseInt(techSelect?.value || "0", 10);
          const t = technicians[idxTech];
          const dest = t ? getDestination(t) : {};
          if (dest.type === "code_ig" || dest.type === "point_relais") {
            destAddr = String(dest.adresse || "").trim();
          } else if (dest.type === "adresse_libre") {
            const l1 = dest.adresse_ligne1 || "";
            const l2 = dest.adresse_ligne2 || "";
            const cp = dest.code_postal || "";
            const ville = dest.ville || "";
            destAddr = [l1, l2, cp, ville]
              .map(x => String(x || "").trim())
              .filter(Boolean)
              .join(" ");
          }
        }

        if (originAddr && destAddr) {
          const url = "https://www.google.com/maps/dir/?api=1" +
            "&origin=" + encodeURIComponent(originAddr) +
            "&destination=" + encodeURIComponent(destAddr) +
            "&travelmode=driving";
          const a = document.createElement("a");
          a.href = url;
          a.target = "_blank";
          a.rel = "noopener noreferrer";
          a.textContent = "Itinéraire";
          itinCell.appendChild(a);
        }
      });
    }

    if (codeInput) {
      codeInput.addEventListener("blur", async () => {
        const raw = (codeInput.value || "").trim();
        if (!raw) return;
        const norm = raw.toUpperCase();
        codeInput.value = norm;

        const info = await fetchItemInfo(norm);
        if (libInput && !libInput.value && info.libelle) {
          libInput.value = info.libelle;
        }
        if (horsNormeCell) {
          if (info.hors_norme) {
            horsNormeCell.textContent = "Oui";
            horsNormeCell.style.background = "#fecaca";
            horsNormeCell.style.color = "#b91c1c";
            horsNormeCell.style.fontWeight = "bold";
          } else {
            horsNormeCell.textContent = "Non";
            horsNormeCell.style.background = "";
            horsNormeCell.style.color = "";
            horsNormeCell.style.fontWeight = "";
          }
        }
      });
    }
  }

  async function renderSelectionSummary() {
    if (!summaryDiv) return;
    if (!currentRows.length) {
      summaryDiv.innerHTML = "";
      return;
    }

    const checked = Array.from(tbodyRows.querySelectorAll("input.stock-select:checked"));
    if (!checked.length) {
      summaryDiv.innerHTML = "<p class='muted'>Aucune ligne sélectionnée.</p>";
      return;
    }

    // Récupérer les lignes de stock sélectionnées
    const rows = [];
    checked.forEach((cb) => {
      const idx = parseInt(cb.dataset.rowIndex || "-1", 10);
      if (!Number.isNaN(idx) && currentRows[idx]) {
        rows.push(currentRows[idx]);
      }
    });

    if (!rows.length) {
      summaryDiv.innerHTML = "<p class='muted'>Aucune ligne sélectionnée.</p>";
      return;
    }

    // Enrichir les lignes avec le flag hors_norme (même logique que la V1)
    await enrichLinesWithHorsNorme(rows);

    // Texte de l'adresse de livraison (identique pour toutes les lignes)
    const destSummaryText = buildDestinationSummaryText();

    const lines = [];
    lines.push("<h4 style='margin:0 0 0.5rem; text-align:center; text-transform:uppercase; letter-spacing:0.05em;'>ORDRE DE LIVRAISON DÉGRADÉ</h4>");
    lines.push("<table><thead><tr>" +
      "<th style='color:#ffffff; background:#1f2937;'>Code article</th>" +
      "<th style='color:#ffffff; background:#1f2937;'>Libellé article</th>" +
      "<th style='color:#ffffff; background:#1f2937;'>Quantité à expédier</th>" +
      "<th style='color:#ffffff; background:#1f2937;'>Code magasin expéditeur</th>" +
      "<th style='color:#ffffff; background:#1f2937;'>Hors norme</th>" +
      "<th style='color:#ffffff; background:#1f2937;'>Adresse de livraison</th>" +
      "<th style='color:#ffffff; background:#1f2937;'>Itinéraire</th>" +
      "<th style='color:#ffffff; background:#1f2937;'>Supprimer</th>" +
      "</tr></thead><tbody>");

    rows.forEach((r, i) => {
      const codeArticle = r.code_article || "";
      const libelle = r.libelle_court_article || "";
      const codeMagasin = r.code_magasin || "";
      const gmapsUrl = buildGoogleMapsDirectionsUrl(r, lastApiData || {});
      const inputId = `qty-${codeMagasin}-${codeArticle}-${i}`;
      const rowIndex = currentRows.indexOf(r);

      const hnText = r.hors_norme ? "Oui" : "Non";
      const hnCell = r.hors_norme
        ? `<td style='background:#fecaca; color:#b91c1c; font-weight:bold;'>${hnText}</td>`
        : `<td>${hnText}</td>`;

      const destText = String(destSummaryText || "").trim();

      const codeArticleCell = codeArticle
        ? `<a href="stock.html?code=${encodeURIComponent(codeArticle)}" target="_blank" rel="noopener noreferrer">${codeArticle}</a>`
        : "";

      lines.push(`<tr data-row-index="${rowIndex}">` +
        `<td>${codeArticleCell}</td>` +
        `<td>${libelle}</td>` +
        `<td><input type="number" id="${inputId}" min="0" step="1" value="1" style="width:6rem; background:#ffffff; color:#111827;" /></td>` +
        `<td>${codeMagasin}</td>` +
        hnCell +
        `<td>${destText}</td>` +
        `<td>${gmapsUrl ? `<a href="${gmapsUrl}" target="_blank" rel="noopener noreferrer">Itinéraire</a>` : ""}</td>` +
        `<td><button type="button" class="omd-remove-line" style="font-size:0.8rem;">Supprimer</button></td>` +
        "</tr>");
    });

    lines.push("</tbody></table>");
    lines.push("<div style='margin-top:0.5rem; text-align:right;'><button type='button' id='omd-add-manual-line' style='font-size:0.85rem;'>Ajouter une ligne manuelle</button></div>");
    summaryDiv.innerHTML = lines.join("");

    const addManualBtn = summaryDiv.querySelector("#omd-add-manual-line");
    if (addManualBtn) {
      addManualBtn.addEventListener("click", () => {
        addManualSummaryLine();
      });
    }

    // Replier automatiquement le panneau carte + stocks une fois le récapitulatif affiché
    collapseStockPanel();
  }

  if (validateBtn) {
    validateBtn.addEventListener("click", () => {
      renderSelectionSummary();
    });
  }

  if (summaryDiv) {
    summaryDiv.addEventListener("click", (event) => {
      const target = event.target;
      if (!(target instanceof HTMLElement)) return;
      if (!target.classList.contains("omd-remove-line")) return;

      const tr = target.closest("tr");
      if (!tr || !tr.parentElement) return;
      tr.parentElement.removeChild(tr);
    });
  }

  const validateOlBtn = document.getElementById("omd-v2-validate");
  if (validateOlBtn) {
    validateOlBtn.addEventListener("click", async () => {
      const payload = buildPayloadFromSelection();
      if (!payload) return;
      // Enrichir les lignes avec le flag hors_norme (logique identique à la V1)
      await enrichLinesWithHorsNorme(payload.lignes || []);
      if (olStatusDiv) olStatusDiv.textContent = "";
      sendMailFromPayload(payload);
    });
  }

    const tr = target.closest("tr");
    if (!tr || !tr.parentElement) return;
    tr.parentElement.removeChild(tr);
  });


const validateOlBtn = document.getElementById("omd-v2-validate");
if (validateOlBtn) {
  validateOlBtn.addEventListener("click", async () => {
    const payload = buildPayloadFromSelection();
    if (!payload) return;
    // Enrichir les lignes avec le flag hors_norme (logique identique à la V1)
    await enrichLinesWithHorsNorme(payload.lignes || []);
    if (olStatusDiv) olStatusDiv.textContent = "";
    sendMailFromPayload(payload);
  });
}
