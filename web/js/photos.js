document.addEventListener("DOMContentLoaded", () => {
  const params = new URLSearchParams(window.location.search);
  const code = (params.get("code") || "").trim();

  const titleEl = document.getElementById("photos-title");
  const container = document.getElementById("photos-container");
  const messageEl = document.getElementById("photos-message");

  if (!code) {
    if (titleEl) titleEl.textContent = "Photos de l'article (code manquant)";
    if (messageEl) messageEl.textContent = "Aucun code article fourni dans l'URL.";
    return;
  }

  if (titleEl) {
    titleEl.textContent = `Photos de l'article ${code}`;
  }

  async function loadPhotos() {
    if (!container) return;
    container.innerHTML = "";
    if (messageEl) messageEl.textContent = "Chargement des photos...";

    try {
      const res = await fetch(API(`/auth/photos/${encodeURIComponent(code)}`));
      if (!res.ok) {
        if (messageEl) messageEl.textContent = `Erreur API photos (${res.status})`;
        return;
      }
      const data = await res.json();
      const files = data.files || [];

      if (!files.length) {
        if (messageEl) messageEl.textContent = "Aucune photo disponible pour cet article.";
        return;
      }

      if (messageEl) messageEl.textContent = "";

      files.forEach((name) => {
        const wrapper = document.createElement("div");
        wrapper.style.border = "1px solid var(--border-color, #ccc)";
        wrapper.style.borderRadius = "4px";
        wrapper.style.padding = "8px";
        wrapper.style.backgroundColor = "var(--card-bg, #111827)";
        wrapper.style.marginBottom = "12px";
        wrapper.style.width = "100%";
        wrapper.style.boxSizing = "border-box";

        const img = document.createElement("img");
        img.src = API(`/auth/photos/raw/${encodeURIComponent(name)}`);
        img.alt = name;
        img.style.display = "block";
        img.style.maxWidth = "100%";
        img.style.height = "auto";
        img.style.maxHeight = "80vh";
        img.style.margin = "0 auto";

        const caption = document.createElement("div");
        caption.textContent = name;
        caption.style.marginTop = "4px";
        caption.style.fontSize = "0.8rem";
        caption.style.textAlign = "center";

        wrapper.appendChild(img);
        wrapper.appendChild(caption);
        container.appendChild(wrapper);
      });
    } catch (e) {
      if (messageEl) messageEl.textContent = "Erreur de communication avec l'API photos.";
    }
  }

  loadPhotos();
});
