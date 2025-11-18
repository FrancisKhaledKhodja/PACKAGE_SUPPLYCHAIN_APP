document.addEventListener("DOMContentLoaded", () => {
  const codeInput = document.getElementById("helios-code");
  const searchBtn = document.getElementById("helios-search");
  const emptyMsg = document.getElementById("helios-empty");
  const content = document.getElementById("helios-content");
  const codeDisplay = document.getElementById("helios-code-display");
  const qtyActive = document.getElementById("helios-qty-active");
  const sitesCount = document.getElementById("helios-sites-count");
  const tbody = document.getElementById("helios-sites-tbody");
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

  if (codeInput) {
    codeInput.addEventListener("keydown", (ev) => {
      if (ev.key === "Enter") {
        ev.preventDefault();
        loadHelios(codeInput.value);
      }
    });
  }
  // Initialisation avec paramètre ?code=...
  (async () => {
    try {
      const url = new URL(window.location.href);
      const codeParam = (url.searchParams.get("code") || "").trim();
      if (!codeParam) return;
      if (codeInput) codeInput.value = codeParam;
      await loadHelios(codeParam);
    } catch (e) {
      // ignore erreur d'URL
    }
  })();
});
