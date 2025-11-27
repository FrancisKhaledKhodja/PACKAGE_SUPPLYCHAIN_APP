document.addEventListener("DOMContentLoaded", () => {
  const statusDiv = document.getElementById("update-status");
  const detailsDiv = document.getElementById("update-details");
  const btnUpdate = document.getElementById("btn-update-data");
  const photosStatus = document.getElementById("photos-update-status");
  const btnUpdatePhotos = document.getElementById("btn-update-photos");

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
});
