document.addEventListener("DOMContentLoaded", () => {
  const statusDiv = document.getElementById("update-status");
  const detailsDiv = document.getElementById("update-details");
  const btnUpdate = document.getElementById("btn-update-data");
  const photosStatus = document.getElementById("photos-update-status");
  const btnUpdatePhotos = document.getElementById("btn-update-photos");
  const assistantForm = document.getElementById("assistant-form");
  const assistantInput = document.getElementById("assistant-question");
  const assistantBtn = document.getElementById("assistant-run");
  const assistantFeedback = document.getElementById("assistant-feedback");
  let assistantPendingWindow = null;

  async function refreshPhotosStats() {
    if (!photosStatus) return;
    try {
      const res = await fetch("http://127.0.0.1:5001/api/auth/photos/stats");
      if (!res.ok) {
        return;
      }
      const data = await res.json();
      const totalNetwork = data.total_network_files ?? 0;
      const totalLocal = data.total_local_files ?? 0;
      const localMatching = data.local_matching_network ?? 0;

      photosStatus.textContent = `Photos : ${totalNetwork} fichier(s) sur le répertoire réseau, ${totalLocal} fichier(s) sur cet ordinateur dont ${localMatching} correspondant(s) à un fichier réseau.`;
    } catch (e) {
    }
  }

  async function refreshStatus() {
    if (!statusDiv || !detailsDiv) return;
    statusDiv.textContent = "Vérification des mises à jour en cours...";
    detailsDiv.innerHTML = "";
    try {
      const res = await fetch("http://127.0.0.1:5001/api/pudo/update-status");
      if (!res.ok) {
        statusDiv.textContent = "Impossible de récupérer le statut des mises à jour (" + res.status + ").";
        return;
      }
      const data = await res.json();
      const items = data.items || [];
      const anyUpdate = !!data.any_update;
      if (!items.length) {
        statusDiv.textContent = "Aucune information de mise à jour disponible.";
        return;
      }
      if (anyUpdate) {
        statusDiv.textContent = "Des mises à jour sont recommandées.";
      } else {
        statusDiv.textContent = "Les données sont à jour.";
      }
      const pending = items.filter(it => it.needs_update);
      if (pending.length) {
        const ul = document.createElement("ul");
        pending.forEach(it => {
          const li = document.createElement("li");
          const key = it.key || "?";
          const src = it.src_mtime_iso || "inconnu";
          const dst = it.dst_mtime_iso || "absent";
          li.textContent = `${key} : source ${src} → destination ${dst}`;
          ul.appendChild(li);
        });
        detailsDiv.appendChild(ul);
      }
    } catch (e) {
      statusDiv.textContent = "Erreur lors de la récupération du statut des mises à jour.";
    }
  }

  if (btnUpdatePhotos) {
    btnUpdatePhotos.addEventListener("click", async () => {
      if (!confirm("Lancer la mise à jour des photos (copie des fichiers .webp manquants depuis le répertoire réseau) ?")) {
        return;
      }
      btnUpdatePhotos.disabled = true;
      btnUpdatePhotos.textContent = "Mise à jour des photos en cours...";
      if (photosStatus) {
        photosStatus.textContent = "Synchronisation des photos en cours...";
      }
      try {
        const res = await fetch("http://127.0.0.1:5001/api/auth/photos/sync", {
          method: "POST",
        });
        if (!res.ok) {
          alert("Erreur lors de la mise à jour des photos (" + res.status + ")");
        } else {
          const data = await res.json();
          const copied = data.copied || 0;
          const already = data.already_present || 0;
          const total = data.total_network_files || 0;
          if (photosStatus) {
            photosStatus.textContent = `Mise à jour des photos terminée : ${copied} fichier(s) copié(s), ${already} déjà présent(s) sur ${total} fichier(s) réseau.`;
          }
          alert("Mise à jour des photos terminée.");
          await refreshPhotosStats();
        }
      } catch (e) {
        alert("Erreur de communication avec l'API pour la mise à jour des photos.");
      } finally {
        btnUpdatePhotos.disabled = false;
        btnUpdatePhotos.textContent = "Lancer la mise à jour des photos";
      }
    });
  }

  if (btnUpdate) {
    btnUpdate.addEventListener("click", async () => {
      if (!confirm("Lancer la mise à jour des données ?")) {
        return;
      }
      btnUpdate.disabled = true;
      btnUpdate.textContent = "Mise à jour en cours...";
      try {
        const res = await fetch("http://127.0.0.1:5001/api/pudo/update", {
          method: "POST",
        });
        if (!res.ok) {
          alert("Erreur lors de la mise à jour (" + res.status + ")");
        } else {
          alert("Mise à jour terminée.");
        }
      } catch (e) {
        alert("Erreur de communication avec l'API.");
      } finally {
        btnUpdate.disabled = false;
        btnUpdate.textContent = "Lancer la mise à jour";
        refreshStatus();
      }
    });
  }

  refreshStatus();
  refreshPhotosStats();

  // Assistant de navigation par question (priorité au LLM on-prem via /api/assistant/query,
  // fallback sur des règles simples côté frontend si le LLM n'est pas disponible).
  async function handleAssistantQuestion() {
    if (!assistantInput) return;
    const raw = assistantInput.value || "";
    const q = raw.trim();
    if (!q) {
      if (assistantFeedback) assistantFeedback.textContent = "Merci de saisir une question.";
      return;
    }

    const lower = q.toLowerCase();

    if (!assistantPendingWindow || assistantPendingWindow.closed) {
      assistantPendingWindow = window.open("about:blank", "_blank");
    }

    // 1) Tenter d'utiliser le LLM via l'API backend
    try {
      if (assistantFeedback) assistantFeedback.textContent = "Interrogation de l'assistant...";
      const resp = await fetch(API("/assistant/query"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ question: q }),
      });

      if (resp.ok) {
        const data = await resp.json();
        const answer = data.answer || "";
        const intent = data.intent || "none";
        const params = data.params || {};
        const target = data.target_page || null;

        console.log("assistant data", data);
        console.log("intent=", intent, "params=", params, "target=", target);

        if (assistantFeedback && answer) {
          assistantFeedback.textContent = answer;
        }

        if (intent === "view_stock_article" && params.code_article) {
          const url = `stock.html?code=${encodeURIComponent(params.code_article)}`;
          let win = assistantPendingWindow && !assistantPendingWindow.closed ? assistantPendingWindow : window.open(url, "_blank");
          if (win) {
            win.location.href = url;
          } else {
            window.location.href = url;
          }
          assistantPendingWindow = null;
          return;
        }
        if (intent === "view_stock_map") {
          const url = new URL(window.location.origin + "/stock_map.html");
          if (params.address) {
            url.searchParams.set("address", params.address);
          }
          if (params.code_article) {
            url.searchParams.set("code", params.code_article);
          }
          const finalUrl = url.toString();
          let win = assistantPendingWindow && !assistantPendingWindow.closed ? assistantPendingWindow : window.open(finalUrl, "_blank");
          if (win) {
            win.location.href = finalUrl;
          } else {
            window.location.href = finalUrl;
          }
          assistantPendingWindow = null;
          return;
        }
        if (intent === "view_nearest_pudo") {
          const url = new URL(window.location.origin + "/stores.html");
          if (params.address) {
            url.searchParams.set("q", params.address);
          }
          const finalUrl = url.toString();
          let win = assistantPendingWindow && !assistantPendingWindow.closed ? assistantPendingWindow : window.open(finalUrl, "_blank");
          if (win) {
            win.location.href = finalUrl;
          } else {
            window.location.href = finalUrl;
          }
          assistantPendingWindow = null;
          return;
        }

        // Si le LLM répond mais sans action claire, on s'arrête là avec juste la réponse texte
        if (answer) {
          return;
        }
        // sinon on tombera dans le fallback règles locales ci-dessous
      } else {
        // LLM non disponible ou erreur serveur, on passe au fallback
        if (assistantFeedback) assistantFeedback.textContent = "L'assistant (LLM) n'a pas pu traiter la question, utilisation d'un routage simplifié...";
      }
    } catch (e) {
      // Erreur réseau / serveur LLM : fallback
      if (assistantFeedback) assistantFeedback.textContent = "L'assistant (LLM) n'a pas pu traiter la question, utilisation d'un routage simplifié...";
    }

    // 2) Fallback : règles simples côté frontend

    // 2.1) Recherche de stock par code article
    const articleMatch = q.match(/\b([A-Z]{2,}\d{3,}|TDF\d{3,})\b/i);
    if (lower.includes("stock") && articleMatch) {
      const codeArticle = articleMatch[1].toUpperCase();
      if (assistantFeedback) assistantFeedback.textContent = `Ouverture d'un nouvel onglet RECHERCHE STOCK pour l'article ${codeArticle}...`;
      const url = `stock.html?code=${encodeURIComponent(codeArticle)}`;
      window.open(url, "_blank");
      return;
    }

    // 2.2) Questions autour des PR / points relais / magasins proches d'une adresse
    // On est volontairement large sur les mots-clés pour mieux couvrir les formulations naturelles
    const mentionsPr =
      lower.includes("point relais") ||
      lower.includes("points relais") ||
      lower.includes("point-relais") ||
      lower.includes("points-relais") ||
      lower.includes(" pr ") ||
      lower.includes("relais");
    const mentionsStore = lower.includes("magasin") || lower.includes("depot") || lower.includes("dépôt");

    if (mentionsPr || mentionsStore) {
      let addr = "";
      const markers = ["qui est le", "qui est", "domicile", "adresse", "au", "au "];
      for (const m of markers) {
        const idx = lower.indexOf(m);
        if (idx !== -1) {
          addr = q.substring(idx + m.length).trim();
          break;
        }
      }
      if (!addr) {
        const cpMatch = q.match(/\b\d{5}\b/);
        if (cpMatch) {
          const cpIndex = q.indexOf(cpMatch[0]);
          addr = q.substring(Math.max(0, cpIndex - 30)).trim();
        }
      }
      if (!addr) {
        // Dernier recours : pour des questions du type "donne les point relais proche de bergerac",
        // on prend le dernier mot non vide comme ville/adresse simple.
        const tokens = q.split(/\s+/).filter(Boolean);
        if (tokens.length) {
          addr = tokens[tokens.length - 1];
        }
      }

      if (mentionsPr) {
        if (assistantFeedback) assistantFeedback.textContent = "Ouverture d'un nouvel onglet Magasins & points relais pour rechercher un PR proche de l'adresse demandée...";
        const url = new URL(window.location.origin + "/stores.html");
        if (addr) {
          url.searchParams.set("q", addr);
        }
        window.open(url.toString(), "_blank");
        return;
      }

      if (mentionsStore && addr) {
        if (assistantFeedback) assistantFeedback.textContent = "Ouverture d'un nouvel onglet carte de localisation du stock centrée sur l'adresse demandée...";
        const url = new URL(window.location.origin + "/stock_map.html");
        url.searchParams.set("address", addr);
        window.open(url.toString(), "_blank");
        return;
      }
    }

    // 2.3) Si aucune règle n'a matché
    if (assistantFeedback) assistantFeedback.textContent = "Je n'ai pas pu interpréter cette question. Essayez par exemple : 'donne moi le stock du code article TDF000629'.";
  }

  if (assistantBtn) {
    assistantBtn.addEventListener("click", handleAssistantQuestion);
  }
  if (assistantForm && assistantInput) {
    assistantInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        handleAssistantQuestion();
      }
    });
  }
});
