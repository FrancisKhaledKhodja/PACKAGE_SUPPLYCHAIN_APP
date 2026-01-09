document.addEventListener("DOMContentLoaded", () => {
  const codeInput = document.getElementById("helios-code");
  const searchBtn = document.getElementById("helios-search");
  const igInput = document.getElementById("helios-code-ig");
  const searchIgBtn = document.getElementById("helios-search-ig");
  const emptyMsg = document.getElementById("helios-empty");
  const content = document.getElementById("helios-content");
  const igEmptyMsg = document.getElementById("helios-ig-empty");
  const igContent = document.getElementById("helios-ig-content");
  const codeDisplay = document.getElementById("helios-code-display");
  const qtyActive = document.getElementById("helios-qty-active");
  const sitesCount = document.getElementById("helios-sites-count");
  const tbody = document.getElementById("helios-sites-tbody");
  const igCodeDisplay = document.getElementById("helios-ig-code-display");
  const igLabel = document.getElementById("helios-ig-label");
  const igAddress = document.getElementById("helios-ig-address");
  const igQtyActive = document.getElementById("helios-ig-qty-active");
  const igItemsCount = document.getElementById("helios-ig-items-count");
  const igParentsTbody = document.getElementById("helios-ig-parents-tbody");
  const igChildrenTbody = document.getElementById("helios-ig-children-tbody");
  const mapContainer = document.getElementById("helios-map");

  let map = null;
  let markersLayer = null;

  function ensureMap() {
    if (!mapContainer) return null;
    if (!map) {
      // centre France par défaut
      map = L.map(mapContainer).setView([47.0, 2.0], 6);
      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
        attribution: '&copy; OpenStreetMap contributors',
      }).addTo(map);
      markersLayer = L.layerGroup().addTo(map);
    }
    return map;
  }

  async function loadHeliosSite(codeIg) {
    const norm = (codeIg || "").trim();
    if (!norm) {
      if (igEmptyMsg) igEmptyMsg.textContent = "Aucun site sélectionné. Recherchez un code IG pour afficher le parc.";
      if (igEmptyMsg) igEmptyMsg.style.display = "block";
      if (igContent) igContent.style.display = "none";
      return;
    }
    try {
      const res = await fetch(API(`/helios/site/${encodeURIComponent(norm)}`));
      if (!res.ok) {
        if (igEmptyMsg) igEmptyMsg.textContent = res.status === 404 ? "Code IG inconnu." : "Erreur API Helios (site).";
        if (igEmptyMsg) igEmptyMsg.style.display = "block";
        if (igContent) igContent.style.display = "none";
        return;
      }
      const data = await res.json();
      const items = data.items || [];
      const parents = data.parents || [];
      const childrenByParent = data.children_by_parent || {};
      const site = data.site || {};

      if (igCodeDisplay) igCodeDisplay.textContent = data.code_ig || norm;
      if (igLabel) igLabel.textContent = site.libelle_long_ig || "";
      if (igAddress) igAddress.textContent = site.postal_address || site.address || "";
      if (igQtyActive) igQtyActive.textContent = (data.quantity_active != null ? String(data.quantity_active) : "0");
      if (igItemsCount) igItemsCount.textContent = (data.active_items != null ? String(data.active_items) : String(items.length));

      function renderChildren(rows) {
        if (!igChildrenTbody) return;
        igChildrenTbody.innerHTML = "";
        (rows || []).forEach(it => {
          const tr = document.createElement("tr");
          const td1 = document.createElement("td");
          td1.textContent = it.code_article != null ? String(it.code_article) : "";
          const tdLabel = document.createElement("td");
          tdLabel.textContent = it.libelle_court_article != null ? String(it.libelle_court_article) : "";
          const td2 = document.createElement("td");
          const q = it.quantity_active;
          td2.textContent = (typeof q === "number") ? q.toFixed(2) : (q != null ? String(q) : "");
          tr.appendChild(td1);
          tr.appendChild(tdLabel);
          tr.appendChild(td2);
          igChildrenTbody.appendChild(tr);
        });
      }

      if (igParentsTbody) {
        igParentsTbody.innerHTML = "";

        // Ligne "TOUS" : afficher tous les fils du site (comportement historique)
        {
          const trAll = document.createElement("tr");
          trAll.style.cursor = "pointer";
          trAll.dataset.parentCode = "__ALL__";

          const td1 = document.createElement("td");
          td1.textContent = "TOUS";
          const tdLabel = document.createElement("td");
          tdLabel.textContent = "Tous les articles fils du site";
          const td2 = document.createElement("td");
          td2.textContent = "";

          trAll.appendChild(td1);
          trAll.appendChild(tdLabel);
          trAll.appendChild(td2);

          trAll.addEventListener("click", () => {
            try {
              Array.from(igParentsTbody.querySelectorAll("tr")).forEach(r => {
                r.style.background = "";
              });
            } catch (e) {}
            trAll.style.background = "rgba(59, 130, 246, 0.15)";
            renderChildren(items);
          });

          // Sélection par défaut
          trAll.style.background = "rgba(59, 130, 246, 0.15)";
          igParentsTbody.appendChild(trAll);
          renderChildren(items);
        }

        parents.forEach((p, idx) => {
          const codeParent = p.code_article_pere != null ? String(p.code_article_pere) : "";
          const tr = document.createElement("tr");
          tr.style.cursor = "pointer";
          tr.dataset.parentCode = codeParent;

          const td1 = document.createElement("td");
          td1.textContent = codeParent;
          const tdLabel = document.createElement("td");
          tdLabel.textContent = p.libelle_court_article_pere != null ? String(p.libelle_court_article_pere) : "";
          const td2 = document.createElement("td");
          const q = p.quantite_pere_actif;
          td2.textContent = (typeof q === "number") ? q.toFixed(2) : (q != null ? String(q) : "");

          tr.appendChild(td1);
          tr.appendChild(tdLabel);
          tr.appendChild(td2);

          tr.addEventListener("click", () => {
            try {
              Array.from(igParentsTbody.querySelectorAll("tr")).forEach(r => {
                r.style.background = "";
              });
            } catch (e) {}
            tr.style.background = "rgba(59, 130, 246, 0.15)";
            const rows = childrenByParent && codeParent ? (childrenByParent[codeParent] || []) : [];
            renderChildren(rows);
          });

          igParentsTbody.appendChild(tr);

          // Pas de sélection automatique d'un parent: le défaut est "TOUS"
        });
      }

      // Fallback si pas de parents (ou pas de colonne parent): afficher la liste existante dans "Fils"
      if ((!parents || parents.length === 0) && igChildrenTbody) {
        renderChildren(items);
      }

      // Carte: centrer sur le site si coords disponibles
      if (mapContainer && typeof L !== "undefined") {
        const lat = site.latitude != null ? Number(site.latitude) : null;
        const lon = site.longitude != null ? Number(site.longitude) : null;
        if (!isNaN(lat) && !isNaN(lon)) {
          const m = ensureMap();
          if (m && markersLayer) {
            markersLayer.clearLayers();
            const label = site.libelle_long_ig || data.code_ig || "";
            const addrParts = [site.postal_address, site.address].filter(Boolean);
            const popup = [label, ...addrParts].filter(Boolean).join("<br>");
            L.marker([lat, lon]).bindPopup(popup).addTo(markersLayer);
            m.setView([lat, lon], 12);
          }
        }
      }

      if (igEmptyMsg) igEmptyMsg.style.display = "none";
      if (igContent) igContent.style.display = "block";
    } catch (e) {
      if (igEmptyMsg) igEmptyMsg.textContent = "Erreur lors du chargement des données Helios (site).";
      if (igEmptyMsg) igEmptyMsg.style.display = "block";
      if (igContent) igContent.style.display = "none";
    }
  }

  async function loadHelios(code) {
    const norm = (code || "").trim();
    if (!norm) {
      if (emptyMsg) emptyMsg.textContent = "Aucun article sélectionné. Recherchez un code article pour afficher le parc.";
      if (emptyMsg) emptyMsg.style.display = "block";
      if (content) content.style.display = "none";
      return;
    }
    try {
      const res = await fetch(API(`/helios/${encodeURIComponent(norm)}`));
      if (!res.ok) {
        if (emptyMsg) emptyMsg.textContent = "Aucun résultat trouvé pour cet article.";
        if (emptyMsg) emptyMsg.style.display = "block";
        if (content) content.style.display = "none";
        return;
      }
      const data = await res.json();
      const sites = data.sites || [];
      if (codeDisplay) codeDisplay.textContent = data.code || norm;
      if (qtyActive) qtyActive.textContent = (data.quantity_active != null ? String(data.quantity_active) : "0");
      if (sitesCount) sitesCount.textContent = (data.active_sites != null ? String(data.active_sites) : String(sites.length));

      if (tbody) {
        tbody.innerHTML = "";
        sites.forEach(s => {
          const tr = document.createElement("tr");
          tr.style.cursor = "pointer";
          const cols = [
            s.code_ig,
            s.libelle_long_ig,
            s.adresse,
            s.code_postal,
            s.quantity_active,
          ];
          cols.forEach(val => {
            const td = document.createElement("td");
            td.textContent = val != null ? String(val) : "";
            tr.appendChild(td);
          });

          tr.addEventListener("click", () => {
            const ig = s && s.code_ig != null ? String(s.code_ig) : "";
            if (!ig) return;
            if (igInput) igInput.value = ig;
            loadHeliosSite(ig);
            try {
              const section = document.getElementById("helios-ig-content");
              if (section) section.scrollIntoView({ behavior: "smooth", block: "start" });
            } catch (e) {}
          });
          tbody.appendChild(tr);
        });
      }

      // Mettre à jour la carte
      if (mapContainer && typeof L !== "undefined") {
        const m = ensureMap();
        if (m && markersLayer) {
          markersLayer.clearLayers();
          const coords = [];
          sites.forEach(s => {
            const lat = s.latitude != null ? Number(s.latitude) : null;
            const lon = s.longitude != null ? Number(s.longitude) : null;
            if (!isNaN(lat) && !isNaN(lon)) {
              coords.push([lat, lon]);
              const label = s.libelle_long_ig || s.code_ig || "";
              const addrParts = [s.adresse, s.code_postal, s.commune].filter(Boolean);
              const addr = addrParts.join(" ");
              const popupLines = [];
              if (label) popupLines.push(String(label));
              if (addr) popupLines.push(String(addr));
              if (s.quantity_active != null) popupLines.push(`Quantité active : ${s.quantity_active}`);
              const popup = popupLines.join("<br>");
              L.marker([lat, lon]).bindPopup(popup).addTo(markersLayer);
            }
          });
          if (coords.length) {
            const bounds = L.latLngBounds(coords);
            m.fitBounds(bounds.pad(0.2));
          } else {
            m.setView([47.0, 2.0], 6);
          }
        }
      }

      if (emptyMsg) emptyMsg.style.display = "none";
      if (content) content.style.display = "block";
    } catch (e) {
      if (emptyMsg) emptyMsg.textContent = "Erreur lors du chargement des données Helios.";
      if (emptyMsg) emptyMsg.style.display = "block";
      if (content) content.style.display = "none";
    }
  }

  if (searchBtn) {
    searchBtn.addEventListener("click", () => {
      loadHelios(codeInput && codeInput.value);
    });
  }

  if (searchIgBtn) {
    searchIgBtn.addEventListener("click", () => {
      loadHeliosSite(igInput && igInput.value);
    });
  }

  if (codeInput) {
    codeInput.addEventListener("keydown", (ev) => {
      if (ev.key === "Enter") {
        ev.preventDefault();
        loadHelios(codeInput.value);
      }
    });
  }

  if (igInput) {
    igInput.addEventListener("keydown", (ev) => {
      if (ev.key === "Enter") {
        ev.preventDefault();
        loadHeliosSite(igInput.value);
      }
    });
  }
  // Initialisation avec paramètre ?code=...
  (async () => {
    try {
      const url = new URL(window.location.href);
      const codeParam = (url.searchParams.get("code") || "").trim();
      const igParam = (url.searchParams.get("ig") || "").trim();
      if (!codeParam) return;
      if (codeInput) codeInput.value = codeParam;
      await loadHelios(codeParam);
      if (igParam) {
        if (igInput) igInput.value = igParam;
        await loadHeliosSite(igParam);
      }
    } catch (e) {
      // ignore erreur d'URL
    }
  })();
});
