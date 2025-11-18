const API_BASE_URL = "http://127.0.0.1:5001/api";

function API(path) {
  return `${API_BASE_URL}${path}`;
}

function scappApplyTheme(theme) {
  const body = document.body;
  if (!body) return;
  const t = theme === "dark" ? "dark" : "light";
  if (t === "dark") {
    body.classList.add("dark-theme");
  } else {
    body.classList.remove("dark-theme");
  }
  try {
    localStorage.setItem("scapp-theme", t);
  } catch (e) {
    /* ignore */
  }
  const btn = document.getElementById("theme-toggle");
  if (btn) {
    btn.textContent = t === "dark" ? "Mode clair" : "Mode sombre";
  }
}

function scappInitTheme() {
  let stored = null;
  try {
    stored = localStorage.getItem("scapp-theme");
  } catch (e) {
    stored = null;
  }
  if (stored !== "dark" && stored !== "light") {
    const prefersDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
    stored = prefersDark ? "dark" : "light";
  }
  scappApplyTheme(stored);
}

function scappRenderHeader() {
  const container = document.getElementById("scapp-header");
  if (!container) return;

  container.innerHTML = `
  <header style="background:#1f2933; color:#fff; padding:1rem 2rem; display:flex; justify-content:space-between; align-items:center; gap:1.5rem;">
    <h1 style="margin:0; font-size:1.25rem;">
      <span class="logo-scapp">
        <span class="logo-part-supply">Supply</span>
        <span class="logo-part-chain">Chain</span>
        <span class="logo-part-app">App</span>
      </span>
    </h1>
    <div style="display:flex; flex-direction:column; gap:0.35rem; align-items:flex-end;">
      <nav>
        <a href="home.html" target="_blank" rel="noopener noreferrer" style="color:#fff; margin-left:1rem; text-decoration:none;">Accueil</a>
        <a href="items.html" target="_blank" rel="noopener noreferrer" style="color:#fff; margin-left:1rem; text-decoration:none;">info_article</a>
        <a href="stock.html" target="_blank" rel="noopener noreferrer" style="color:#fff; margin-left:1rem; text-decoration:none;">RECHERCHE_STOCK</a>
        <a href="stock_detailed.html" target="_blank" rel="noopener noreferrer" style="color:#fff; margin-left:1rem; text-decoration:none;">Stock détaillé</a>
        <a href="helios.html" target="_blank" rel="noopener noreferrer" style="color:#fff; margin-left:1rem; text-decoration:none;">Parc Helios</a>
        <a href="stores.html" target="_blank" rel="noopener noreferrer" style="color:#fff; margin-left:1rem; text-decoration:none;">Magasins & points relais</a>
        <a href="downloads.html" target="_blank" rel="noopener noreferrer" style="color:#fff; margin-left:1rem; text-decoration:none;">Téléchargements</a>
        <a href="technician.html" target="_blank" rel="noopener noreferrer" style="color:#fff; margin-left:1rem; text-decoration:none;">Sélection du technicien</a>
        <a href="technician_assignments.html" target="_blank" rel="noopener noreferrer" style="color:#fff; margin-left:1rem; text-decoration:none;">Affectation technicien ↔️ PUDO</a>
      </nav>
      <div id="scapp-update-banner" style="font-size:0.75rem; color:#facc15;"></div>
      <button id="theme-toggle" type="button" class="btn-theme-toggle">Mode sombre</button>
    </div>
  </header>
  `;

  const btn = document.getElementById("theme-toggle");
  if (btn) {
    btn.addEventListener("click", () => {
      const isDark = document.body.classList.contains("dark-theme");
      scappApplyTheme(isDark ? "light" : "dark");
    });
  }

  scappInitTheme();
}

async function scappCheckUpdates() {
  const banner = document.getElementById("scapp-update-banner");
  if (!banner) return;
  try {
    const res = await fetch(API("/updates/status"));
    if (!res.ok) return;
    const data = await res.json();
    if (!data || !data.has_changes) {
      banner.textContent = "";
      return;
    }
    let txt = "Données mises à jour récemment";
    if (data.timestamp) {
      const d = new Date(data.timestamp * 1000);
      const hh = String(d.getHours()).padStart(2, "0");
      const mm = String(d.getMinutes()).padStart(2, "0");
      txt = `Données mises à jour à ${hh}h${mm}`;
    }
    banner.textContent = txt;
  } catch (e) {
    // on ignore les erreurs de statut
  }
}

document.addEventListener("DOMContentLoaded", () => {
  scappRenderHeader();
  scappCheckUpdates();
  setInterval(scappCheckUpdates, 60000);
  if (!document.getElementById("scapp-header")) {
    scappInitTheme();
    const btn = document.getElementById("theme-toggle");
    if (btn) {
      btn.addEventListener("click", () => {
        const isDark = document.body.classList.contains("dark-theme");
        scappApplyTheme(isDark ? "light" : "dark");
      });
    }
  }
});
