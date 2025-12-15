document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("form-stores");
  const addressInput = document.getElementById("address");
  const radiusInput = document.getElementById("radius_km");
  const statusDiv = document.getElementById("stores-status");
  const countDiv = document.getElementById("stores-count");
  const geocodedDiv = document.getElementById("stores-geocoded");
  const theadRow = document.getElementById("stores-thead-row");
  const tbodyRows = document.getElementById("stores-tbody-rows");
  const pudoCountDiv = document.getElementById("pudo-count");
  const pudoTheadRow = document.getElementById("pudos-thead-row");
  const pudoTbodyRows = document.getElementById("pudos-tbody-rows");
  const exportStoresBtn = document.getElementById("export-stores-csv");
  const exportPudosBtn = document.getElementById("export-pudos-csv");

  if (!form) return;

  let map = null;
  let storesLayer = null;
  let pudoLayer = null;
  let currentStoreRows = [];
  let currentPudoRows = [];

  // Pré-remplissage de l'adresse depuis le paramètre q de l'URL (appelé par l'assistant)
  try {
    const params = new URLSearchParams(window.location.search);
    const qParam = params.get("q");
    if (qParam && addressInput) {
      addressInput.value = qParam;
      // Lancer automatiquement la recherche pour éviter à l'utilisateur de re-cliquer
      setTimeout(() => {
        if (statusDiv) {
          statusDiv.textContent = "Recherche en cours...";
        }
        if (typeof form.requestSubmit === "function") {
          form.requestSubmit();
          return;
        }
        try {
          form.dispatchEvent(new SubmitEvent("submit", { bubbles: true, cancelable: true }));
        } catch (e) {
          form.dispatchEvent(new Event("submit", { bubbles: true, cancelable: true }));
        }
      }, 0);
    }
  } catch (e) {
    // Silencieux : si URLSearchParams n'est pas dispo, on ne fait rien
  }

  function ensureMap(lat, lon) {
    if (!window.L) return;
    if (!map) {
      map = L.map("map").setView([lat, lon], 11);
      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
        attribution: "&copy; OpenStreetMap contributors",
      }).addTo(map);
      storesLayer = L.layerGroup().addTo(map);
      pudoLayer = L.layerGroup().addTo(map);
      setTimeout(() => {
        try {
          map.invalidateSize();
        } catch (e) {
        }
      }, 0);
    } else {
      map.setView([lat, lon], 11);
      storesLayer.clearLayers();
      pudoLayer.clearLayers();
      setTimeout(() => {
        try {
          map.invalidateSize();
        } catch (e) {
        }
      }, 0);
    }
  }

  function tryEnsureMapFromRows(rows) {
    if (!rows || !rows.length) return;
    if (map) return;
    const first = rows[0] || {};
    const lat = first.latitude_right ?? first.latitude;
    const lon = first.longitude_right ?? first.longitude;
    if (lat != null && lon != null) {
      ensureMap(lat, lon);
    }
  }

  form.addEventListener("submit", async () => {
    const address = addressInput.value.trim();
    const radius = parseFloat(radiusInput.value || "10");
    const typeCheckboxes = Array.from(document.querySelectorAll("input[name='store_types']:checked"));
    const storeTypes = typeCheckboxes.map(cb => cb.value);
    const prCheckboxes = Array.from(document.querySelectorAll("input[name='pr_types']:checked"));
    const prTypes = prCheckboxes.map(cb => cb.value);

    if (!address) {
      statusDiv.textContent = "Merci de saisir une adresse.";
      return;
    }

    statusDiv.textContent = "Recherche en cours...";
    countDiv.textContent = "";
    geocodedDiv.textContent = "";
    theadRow.innerHTML = "";
    tbodyRows.innerHTML = "";
    if (pudoCountDiv) pudoCountDiv.textContent = "";
    if (pudoTheadRow) pudoTheadRow.innerHTML = "";
    if (pudoTbodyRows) pudoTbodyRows.innerHTML = "";

    try {
      const promises = [];

      // Appel magasins uniquement si au moins un type est sélectionné
      if (storeTypes.length) {
        promises.push(
          fetch(API("/stores/nearby-address"), {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify({
              address,
              radius_km: radius,
              store_types: storeTypes,
            }),
          })
        );
      } else {
        // Aucun type de magasin sélectionné : on nettoie la partie magasins
        countDiv.textContent = "";
        theadRow.innerHTML = "";
        tbodyRows.innerHTML = "";
        if (storesLayer && map) {
          storesLayer.clearLayers();
        }
      }

      // Appel PR uniquement si au moins un type PR est sélectionné
      if (prTypes.length) {
        promises.push(
          fetch(API("/pudo/nearby-address"), {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify({
              address,
              radius_km: radius,
              enseignes: prTypes,
            }),
          })
        );
      } else {
        if (pudoCountDiv) pudoCountDiv.textContent = "";
        if (pudoTheadRow) pudoTheadRow.innerHTML = "";
        if (pudoTbodyRows) pudoTbodyRows.innerHTML = "";
      }

      // Si aucun filtre n'est sélectionné (ni magasins ni PR), on arrête là
      if (!storeTypes.length && !prTypes.length) {
        statusDiv.textContent = "Aucun type de magasin ni de point relais sélectionné (cochez au moins un filtre).";
        return;
      }

      const [storesResp, pudoResp] = await Promise.all([
        // Pour conserver la structure, on remet null si pas d'appel correspondant
        storeTypes.length ? promises[0] : Promise.resolve(null),
        prTypes.length ? (storeTypes.length ? promises[1] : promises[0]) : Promise.resolve(null),
      ]);

      // ---- Traitement magasins ----
      let storeRows = [];
      let centerLat = null;
      let centerLon = null;

      if (storesResp) {
        if (!storesResp.ok) {
          statusDiv.textContent = "Erreur API magasins (" + storesResp.status + ")";
        } else {
          const storesData = await storesResp.json();
          storeRows = storesData.rows || [];
          currentStoreRows = storeRows;

          if (storesData.geocoded_address) {
            geocodedDiv.textContent = "Adresse géocodée : " + storesData.geocoded_address;
          }

          centerLat = storesData.center_lat;
          centerLon = storesData.center_lon;
          if (centerLat != null && centerLon != null) {
            ensureMap(centerLat, centerLon);
          }

          if (!storeRows.length) {
            countDiv.textContent = "Aucun magasin trouvé.";
          } else {
            countDiv.textContent = storeRows.length + " magasin(s) trouvé(s)";
          }
        }
      }

      if (storeRows.length) {
        const first = storeRows[0];
        const columns = [
          "code_magasin",
          "type_de_depot",
          "adresse_1",
          "adresse_2",
          "code_postal",
          "ville",
          "distance",
        ].filter(c => Object.prototype.hasOwnProperty.call(first, c));

        theadRow.innerHTML = "";
        for (const col of columns) {
          const th = document.createElement("th");
          th.textContent = col === "distance" ? "distance (km)" : col;
          theadRow.appendChild(th);
        }

        tbodyRows.innerHTML = "";
        if (storesLayer && map) {
          storesLayer.clearLayers();
        }
        for (const row of storeRows) {
          const tr = document.createElement("tr");
          for (const col of columns) {
            const td = document.createElement("td");
            let val = row[col];
            if (col === "distance" && typeof val === "number") {
              td.textContent = val.toFixed(2);
            } else {
              td.textContent = val != null ? String(val) : "";
            }
            tr.appendChild(td);
          }
          tbodyRows.appendChild(tr);

          if (storesLayer && map) {
            const lat = row.latitude_right || row.latitude;
            const lon = row.longitude_right || row.longitude;
            if (lat != null && lon != null) {
              const marker = L.marker([lat, lon], {
                icon: L.icon({
                  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
                  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
                  iconSize: [25, 41],
                  iconAnchor: [12, 41],
                  shadowSize: [41, 41],
                })
              });
              const label = `${row.code_magasin || ""} - ${row.ville || ""}`;
              marker.bindPopup(label);
              marker.addTo(storesLayer);
            }
          }
        }
      }

      // ---- Traitement points relais ----
      if (pudoResp) {
        if (!pudoResp.ok) {
          statusDiv.textContent = "Erreur API points relais (" + pudoResp.status + ")";
        } else {
          const pudoData = await pudoResp.json();
          const pudoRows = pudoData.rows || [];
          currentPudoRows = pudoRows;

          if (!map) {
            const centerLat = pudoData.center_lat;
            const centerLon = pudoData.center_lon;
            if (centerLat != null && centerLon != null) {
              ensureMap(centerLat, centerLon);
            }
          }

          if (!map) {
            tryEnsureMapFromRows(pudoRows);
          }

          if (pudoRows.length) {
            if (pudoCountDiv) pudoCountDiv.textContent = pudoRows.length + " point(s) relais";
            const firstP = pudoRows[0];
            const pudoCols = [
              "code_point_relais",
              "enseigne",
              "adresse_1",
              "code_postal",
              "ville",
              "categorie_pr_chronopost",
              "nom_prestataire",
              "distance",
            ].filter(c => Object.prototype.hasOwnProperty.call(firstP, c));

            if (pudoTheadRow) {
              pudoTheadRow.innerHTML = "";
              for (const col of pudoCols) {
                const th = document.createElement("th");
                th.textContent = col === "distance" ? "distance (km)" : col;
                pudoTheadRow.appendChild(th);
              }
            }

            if (pudoTbodyRows) {
              pudoTbodyRows.innerHTML = "";
              if (pudoLayer && map) {
                pudoLayer.clearLayers();
              }
              for (const row of pudoRows) {
                const tr = document.createElement("tr");
                for (const col of pudoCols) {
                  const td = document.createElement("td");
                  let val = row[col];
                  if (col === "distance" && typeof val === "number") {
                    td.textContent = val.toFixed(2);
                  } else {
                    td.textContent = val != null ? String(val) : "";
                  }
                  tr.appendChild(td);
                }
                pudoTbodyRows.appendChild(tr);

                if (pudoLayer && map) {
                  const lat = row.latitude;
                  const lon = row.longitude;
                  if (lat != null && lon != null) {
                    const enseigne = (row.enseigne || "").toString().toLowerCase();
                    const prestataire = (row.nom_prestataire || "").toString().toLowerCase();

                    let stroke = "#2563eb";
                    let fill = "#60a5fa";

                    if (prestataire === "lm2s" || enseigne.includes("lm2s")) {
                      stroke = "#b91c1c";
                      fill = "#ef4444";
                    }
                    else if (prestataire === "tdf" || enseigne.includes("tdf")) {
                      stroke = "#000000";
                      fill = "#111827";
                    }

                    const marker = L.circleMarker([lat, lon], {
                      radius: 6,
                      color: stroke,
                      fillColor: fill,
                      fillOpacity: 0.9,
                    });
                    const label = `${row.code_point_relais || ""} - ${row.ville || ""}`;
                    marker.bindPopup(label);
                    marker.addTo(pudoLayer);
                  }
                }
              }
            }
          } else if (pudoCountDiv) {
            pudoCountDiv.textContent = "Aucun point relais trouvé.";
          }
        }
      }

      statusDiv.textContent = "";
    } catch (e) {
      statusDiv.textContent = "Erreur de communication avec l'API.";
    }
  });

  function exportCsvFromRows(rows, filename) {
    if (!rows || !rows.length) {
      alert("Aucune donnée à exporter.");
      return;
    }
    const columns = Object.keys(rows[0]);
    const escapeCell = (val) => {
      if (val == null) return "";
      const s = String(val).replace(/"/g, '""');
      return '"' + s + '"';
    };
    const lines = [];
    lines.push(columns.map(escapeCell).join(";"));
    for (const row of rows) {
      const line = columns.map(col => escapeCell(row[col])).join(";");
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

  if (exportStoresBtn) {
    exportStoresBtn.addEventListener("click", () => {
      exportCsvFromRows(currentStoreRows, "magasins.csv");
    });
  }

  if (exportPudosBtn) {
    exportPudosBtn.addEventListener("click", () => {
      exportCsvFromRows(currentPudoRows, "points_relais.csv");
    });
  }
});
