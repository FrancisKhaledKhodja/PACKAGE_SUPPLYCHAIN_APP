const API_BASE_URL = "http://127.0.0.1:5001/api";

function API(path) {
  return `${API_BASE_URL}${path}`;
}

function scappInitSingleTabLinks() {
  const links = document.querySelectorAll("a[target='_blank']");
  links.forEach((a) => {
    const href = a.getAttribute("href");
    if (!href) return;
    const name = "scapp-" + href.replace(/[^\w-]/g, "_");
    a.addEventListener("click", (e) => {
      e.preventDefault();
      window.open(href, name);
    });
  });
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
        <a href="home.html" target="_blank" rel="noopener noreferrer" style="color:#fff; margin-left:1rem; text-decoration:none;">ACCUEIL</a>
        <a href="stock.html" target="_blank" rel="noopener noreferrer" style="color:#fff; margin-left:1rem; text-decoration:none;">RECHERCHE STOCK</a>
        <div class="scapp-dropdown" style="position:relative; display:inline-block; margin-left:1rem;">
          <button type="button" class="scapp-dropdown-toggle" style="background:none; border:none; color:#fff; cursor:pointer; font:inherit; padding:0;">
            STOCK ▾
          </button>
          <div class="scapp-dropdown-menu" style="display:none; position:absolute; right:0; background:#111827; padding:0.5rem 0; min-width:220px; box-shadow:0 10px 15px -3px rgba(0,0,0,0.5); border-radius:0.375rem; z-index:50;">
            <a href="stock_detailed.html" target="_blank" rel="noopener noreferrer" style="display:block; color:#fff; padding:0.35rem 0.75rem; text-decoration:none; white-space:nowrap;">STOCK DÉTAILLÉ</a>
            <a href="stock_hyper_detaille.html" target="_blank" rel="noopener noreferrer" style="display:block; color:#fff; padding:0.35rem 0.75rem; text-decoration:none; white-space:nowrap;">STOCK HYPER DÉTAILLÉ</a>
          </div>
        </div>
        <a href="stock_map.html" target="_blank" rel="noopener noreferrer" style="color:#fff; margin-left:1rem; text-decoration:none;">LOCALISATION STOCK</a>
        <a href="items.html" target="_blank" rel="noopener noreferrer" style="color:#fff; margin-left:1rem; text-decoration:none;">CONSULTATION ARTICLE</a>
        <a href="helios.html" target="_blank" rel="noopener noreferrer" style="color:#fff; margin-left:1rem; text-decoration:none;">PARC HELIOS</a>
        <a href="ol_mode_degrade_v2.html" target="_blank" rel="noopener noreferrer" style="color:#fff; margin-left:1rem; text-decoration:none;">OL MODE DÉGRADÉ</a>
        <div class="scapp-dropdown" style="position:relative; display:inline-block; margin-left:1rem;">
          <button type="button" class="scapp-dropdown-toggle" style="background:none; border:none; color:#fff; cursor:pointer; font:inherit; padding:0;">
            CONSULTATION PR ET MAGASIN ▾
          </button>
          <div class="scapp-dropdown-menu" style="display:none; position:absolute; right:0; background:#111827; padding:0.5rem 0; min-width:260px; box-shadow:0 10px 15px -3px rgba(0,0,0,0.5); border-radius:0.375rem; z-index:50;">
            <a href="technician.html" target="_blank" rel="noopener noreferrer" style="display:block; color:#fff; padding:0.35rem 0.75rem; text-decoration:none; white-space:nowrap;">CONSULTATION MAGASIN</a>
            <a href="stores.html" target="_blank" rel="noopener noreferrer" style="display:block; color:#fff; padding:0.35rem 0.75rem; text-decoration:none; white-space:nowrap;">RECHERCHE PR ET MAGASINS PROCHES D'UNE ADRESSE</a>
            <a href="technician_assignments.html" target="_blank" rel="noopener noreferrer" style="display:block; color:#fff; padding:0.35rem 0.75rem; text-decoration:none; white-space:nowrap;">CONSULTATION PR TECHNICIEN</a>
            <a href="technician_admin.html" target="_blank" rel="noopener noreferrer" style="display:block; color:#fff; padding:0.35rem 0.75rem; text-decoration:none; white-space:nowrap;">ADMINISTRATION PR</a>
          </div>
        </div>
        <a href="downloads.html" target="_blank" rel="noopener noreferrer" style="color:#fff; margin-left:1rem; text-decoration:none;">TÉLÉCHARGEMENTS</a>
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

  const dropdowns = container.querySelectorAll(".scapp-dropdown");
  dropdowns.forEach((dd) => {
    const toggle = dd.querySelector(".scapp-dropdown-toggle");
    const menu = dd.querySelector(".scapp-dropdown-menu");
    if (!toggle || !menu) return;
    let open = false;

    const show = () => {
      menu.style.display = "block";
      open = true;
    };

    const hide = () => {
      menu.style.display = "none";
      open = false;
    };

    toggle.addEventListener("click", (e) => {
      e.preventDefault();
      if (open) {
        hide();
      } else {
        show();
      }
    });

    dd.addEventListener("mouseleave", () => {
      if (open) hide();
    });
  });

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
  scappInitSingleTabLinks();
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
