document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("form-stock-map");
  const codeInput = document.getElementById("code_article");
  const codeIgInput = document.getElementById("code_ig");
  const addressInput = document.getElementById("address");
  const horsTransitInput = document.getElementById("hors_transit");
  const stockFiltersToggle = document.getElementById("stock-filters-toggle");
  const statusDiv = document.getElementById("stock-map-status");
  const countDiv = document.getElementById("stock-map-count");
  const articleInfoDiv = document.getElementById("stock-map-article-info");
  const centerInfoDiv = document.getElementById("stock-map-center-info");
  const theadRow = document.getElementById("stock-map-thead-row");
  const tbodyRows = document.getElementById("stock-map-tbody-rows");
  const exportBtn = document.getElementById("btn-export-stock-map");

  if (!form) return;

  // Pré-remplissage depuis l'URL (appelé par l'assistant)
  try {
    const params = new URLSearchParams(window.location.search || "");
    const codeParam = (params.get("code") || "").trim();
    const addressParam = (params.get("address") || "").trim();

    let shouldAutoSubmit = false;
    if (codeParam && codeInput) {
      codeInput.value = codeParam;
      shouldAutoSubmit = true;
    }
    if (addressParam && addressInput) {
      addressInput.value = addressParam;
      shouldAutoSubmit = true;
    }

    if (shouldAutoSubmit) {
      setTimeout(() => {
        try {
          if (typeof form.requestSubmit === "function") {
            form.requestSubmit();
            return;
          }
          form.dispatchEvent(new Event("submit", { bubbles: true, cancelable: true }));
        } catch (e) {
          // ignore
        }
      }, 0);
    }
  } catch (e) {
    // ignore
  }

  let map = null;
  let storesLayer = null;
  let refLayer = null;
  let currentRows = [];

  const TYPE_DEPOT_COLORS = {
    "NATIONAL": "#2563eb",      // bleu
    "LOCAL": "#16a34a",         // vert
    "REO": "#dc2626",          // rouge
    "PIED DE SITE": "#d97706",  // orange
    "EMBARQUE": "#0d9488",      // teal
    "LABORATOIRE": "#ec4899",   // rose
    "DIVERS": "#6b7280",        // gris
    "FOURNISSEURS": "#ea580c",  // orange foncé
    "SOUS TRAITANTS": "#22c55e",// vert clair
    "RESERVE": "#4b5563",       // gris foncé
    "DATACENTER": "#0891b2",    // cyan
  };

  const getColorForTypeDepot = (type) => {
    if (!type) return "#1f2937";
    return TYPE_DEPOT_COLORS[type] || "#1f2937";
  };

  // Gestion de la case globale "Tout cocher / décocher" pour les filtres stock
  if (stockFiltersToggle) {
    const getAllStockFilterCheckboxes = () => {
      const typeDepot = Array.from(document.querySelectorAll("input[name='type_de_depot']"));
      const codeQualite = Array.from(document.querySelectorAll("input[name='code_qualite']"));
      const flagStock = Array.from(document.querySelectorAll("input[name='flag_stock_d_m']"));
      const others = [];
      if (horsTransitInput) {
        others.push(horsTransitInput);
      }
      return [...typeDepot, ...codeQualite, ...flagStock, ...others];
    };

    const syncToggleFromChildren = () => {
      const all = getAllStockFilterCheckboxes();
      if (!all.length) return;
      const allChecked = all.every(cb => cb.checked);
      stockFiltersToggle.checked = allChecked;
    };

    stockFiltersToggle.addEventListener("change", () => {
      const all = getAllStockFilterCheckboxes();
      all.forEach(cb => {
        cb.checked = stockFiltersToggle.checked;
      });
    });

    const allFilters = getAllStockFilterCheckboxes();
    allFilters.forEach(cb => {
      cb.addEventListener("change", () => {
        syncToggleFromChildren();
      });
    });

    // Initialisation de l'état de la case globale selon les filtres existants
    syncToggleFromChildren();
  }

  // Export Excel (CSV) des résultats courants
  if (exportBtn) {
    exportBtn.addEventListener("click", async () => {
      if (!currentRows || !currentRows.length) {
        statusDiv.textContent = "Aucun résultat à exporter.";
        return;
      }

      const rawCode = (codeInput.value || "").trim();
      if (!rawCode) {
        statusDiv.textContent = "Merci de saisir un code article avant d'exporter.";
        return;
      }

      const typeDepotValues = Array.from(document.querySelectorAll("input[name='type_de_depot']:checked")).map(cb => cb.value);
      const codeQualiteValues = Array.from(document.querySelectorAll("input[name='code_qualite']:checked")).map(cb => cb.value);
      const flagStockValues = Array.from(document.querySelectorAll("input[name='flag_stock_d_m']:checked")).map(cb => cb.value);
      const horsTransitOnly = horsTransitInput ? !!horsTransitInput.checked : false;

      statusDiv.textContent = "Préparation de l'export en cours...";

      try {
        const resp = await fetch(API("/stores/stock-map/export"), {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({
            code_article: rawCode,
            type_de_depot: typeDepotValues,
            code_qualite: codeQualiteValues,
            flag_stock_d_m: flagStockValues,
            hors_transit_only: horsTransitOnly,
          }),
        });

        if (!resp.ok) {
          let msg = "Erreur lors de l'export.";
          try {
            const err = await resp.json();
            if (err && err.error === "no_results") {
              msg = "Aucun résultat à exporter avec les filtres actuels.";
            } else if (err && typeof err.error === "string") {
              msg = `Erreur export (${err.error}).`;
            }
          } catch (_) {}
          statusDiv.textContent = msg;
          return;
        }

        const blob = await resp.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "localisation_stock.csv";
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
        statusDiv.textContent = "Export terminé.";
      } catch (e) {
        statusDiv.textContent = "Erreur de communication lors de l'export.";
      }
    });
  }

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
    const codeIg = (codeIgInput ? codeIgInput.value : "").trim();
    const address = (addressInput ? addressInput.value : "").trim();

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

      // Gestion potentiel de plusieurs codes article séparés par des ";"
      const codes = rawCode
        .split(";")
        .map((c) => (c || "").trim().toUpperCase())
        .filter((c) => !!c);

      let allRows = [];
      let firstApiData = null;

      if (!codes.length) {
        // Cas particulier : aucun code article fourni ⇒
        // on récupère uniquement les magasins filtrés par type de dépôt
        const resp = await fetch(API("/stores/stock-map"), {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({
            // pas de code_article
            code_ig: codeIg || undefined,
            address: address || undefined,
            type_de_depot: typeDepotValues,
            // les critères qualité / flag / transit sont ignorés côté API
            code_qualite: [],
            flag_stock_d_m: [],
            hors_transit_only: false,
          }),
        });

        if (!resp.ok) {
          statusDiv.textContent = `Erreur API (${resp.status})`;
          return;
        }

        const dataPart = await resp.json();
        allRows = dataPart.rows || [];
        firstApiData = { data: dataPart, code: null };
      } else {
        // Cas historique : un ou plusieurs codes article fournis
        for (let i = 0; i < codes.length; i += 1) {
          const code = codes[i];
          const resp = await fetch(API("/stores/stock-map"), {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify({
              code_article: code,
              code_ig: codeIg || undefined,
              address: address || undefined,
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
      }

      const data = firstApiData ? firstApiData.data : { rows: allRows };
      const rows = allRows;
      currentRows = rows;

      if (!rows.length) {
        statusDiv.textContent = "Aucun magasin avec ces codes article en stock (selon les filtres qualité/stock/type de dépôt).";
        countDiv.textContent = "0 magasin";
        return;
      }

      // Tri des résultats par distance croissante (lignes sans distance en dernier)
      rows.sort((a, b) => {
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
      } else if (codes.length > 1) {
        // Afficher simplement la liste des codes saisis
        articleInfoDiv.textContent = codes.join(" ; ");
      } else {
        // Aucun code article : pas de récap article en en-tête
        articleInfoDiv.textContent = "";
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
      const columns = [
        "code_article",
        "code_magasin",
        "libelle_magasin",
        "type_de_depot",
        "code_qualite",
        "flag_stock_d_m",
        "qte_stock_total",
        "distance_km",
        "adresse",
      ].filter(c => Object.prototype.hasOwnProperty.call(first, c));

      theadRow.innerHTML = "";
      for (const col of columns) {
        const th = document.createElement("th");
        th.textContent = col;
        theadRow.appendChild(th);
      }
      // Colonne supplémentaire pour l'itinéraire Google Maps
      const thDir = document.createElement("th");
      thDir.textContent = "Itinéraire";
      theadRow.appendChild(thDir);

      tbodyRows.innerHTML = "";
      for (const row of rows) {
        const tr = document.createElement("tr");
        for (const col of columns) {
          const td = document.createElement("td");
          let val = row[col];
          if ((col === "qte_stock_total" || col === "distance_km") && typeof val === "number") {
            td.textContent = val.toFixed(2);
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
      }

      const withCoords = rows.filter(r => r.latitude != null && r.longitude != null);
      if (withCoords.length) {
        // Centre prioritaire : center_lat/center_lon si fournis par l'API, sinon premier magasin
        const centerLat = typeof data.center_lat === "number" ? data.center_lat : withCoords[0].latitude;
        const centerLon = typeof data.center_lon === "number" ? data.center_lon : withCoords[0].longitude;
        ensureMap(centerLat, centerLon, 6);

        if (refLayer && typeof data.center_lat === "number" && typeof data.center_lon === "number") {
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
              type_de_depot: r.type_de_depot || "",
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
          const color = getColorForTypeDepot(g.type_de_depot);
          const marker = L.circleMarker([g.lat, g.lon], {
            radius: 7,
            color,
            fillColor: color,
            fillOpacity: 0.9,
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
            lines.push(`${g.distance_km.toFixed(2)} km`);
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
});
