const API_BASE_URL = (() => {
  try {
    const h = window.location.hostname || "127.0.0.1";
    const proto = window.location.protocol || "http:";
    return `${proto}//${h}:5001/api`;
  } catch (e) {
    return "http://127.0.0.1:5001/api";
  }
})();

function scappStartHeartbeat() {
  if (window.__scappHeartbeatTimer) return;
  const send = () => {
    try {
      const url = API("/app/ping");
      if (navigator && typeof navigator.sendBeacon === "function") {
        navigator.sendBeacon(url, "");
        return;
      }
      fetch(url, { method: "POST", keepalive: true }).catch(() => {});
    } catch (e) {
      // ignore
    }
  };
  send();
  window.__scappHeartbeatTimer = setInterval(send, 10000);
}

function scappStopHeartbeat() {
  const t = window.__scappHeartbeatTimer;
  if (t) {
    clearInterval(t);
    window.__scappHeartbeatTimer = null;
  }
}

function scappBroadcastExit() {
  try {
    if (window.BroadcastChannel) {
      const ch = new BroadcastChannel("scapp-exit");
      ch.postMessage({ type: "exit" });
      try { ch.close(); } catch (e) {}
      return;
    }
  } catch (e) {
    // ignore
  }
  try {
    localStorage.setItem("scapp-exit", String(Date.now()));
  } catch (e) {
    // ignore
  }
}

function scappHandleExitSignal() {
  scappStopHeartbeat();
  try {
    window.location.replace("about:blank");
  } catch (e) {
    // ignore
  }
  setTimeout(() => {
    try { window.close(); } catch (e) {}
  }, 50);
}

function scappInitExitListener() {
  try {
    if (window.BroadcastChannel) {
      const ch = new BroadcastChannel("scapp-exit");
      ch.addEventListener("message", (ev) => {
        const msg = ev && ev.data ? ev.data : null;
        if (msg && msg.type === "exit") {
          scappHandleExitSignal();
        }
      });
    }
  } catch (e) {
    // ignore
  }
  try {
    window.addEventListener("storage", (e) => {
      if (e && e.key === "scapp-exit") {
        scappHandleExitSignal();
      }
    });
  } catch (e) {
    // ignore
  }
}

function scappInitExitButton() {
  const btn = document.getElementById("scapp-exit");
  if (!btn) return;
  btn.addEventListener("click", () => {
    const ok = confirm("Quitter SupplyChainApp ?\n\nCela va arrêter l'application (frontend + API).");
    if (!ok) return;
    scappBroadcastExit();
    try {
      fetch(API("/app/exit"), { method: "POST", keepalive: true }).catch(() => {});
    } catch (e) {
      // ignore
    }
    scappHandleExitSignal();
  });
}

function API(path) {
  return `${API_BASE_URL}${path}`;
}

async function scappFetchAppInfo() {
  try {
    const res = await fetch(API("/app/info"), {
      method: "GET",
      credentials: "include",
    });
    if (!res.ok) return {};
    const data = await res.json().catch(() => ({}));
    return data && typeof data === "object" ? data : {};
  } catch (e) {
    return {};
  }
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

async function scappRenderHeader() {
  const container = document.getElementById("scapp-header");
  if (!container) return;

  const appInfo = await scappFetchAppInfo();
  const hideLlmRag = !!(appInfo && appInfo.hide_llm_rag);
  const version = appInfo && appInfo.version ? String(appInfo.version).trim() : "";
  const versionHtml = version ? `<span class="scapp-app-version">v${version}</span>` : "";

  const llmRagLink = hideLlmRag
    ? ""
    : '<a href="assistant_rag.html" target="_blank" rel="noopener noreferrer" class="scapp-nav-link scapp-nav-link--spaced">ASSISTANT (LLM+RAG)</a>';

  container.innerHTML = `
  <header class="scapp-header">
    <h1 class="scapp-header-title">
      <span class="logo-scapp">
        <span class="logo-part-supply">Supply</span>
        <span class="logo-part-chain">Chain</span>
        <span class="logo-part-app">App</span>
      </span>
      ${versionHtml}
    </h1>
    <div class="scapp-header-right">
      <nav class="scapp-nav">
        <a href="home.html" target="_blank" rel="noopener noreferrer" class="scapp-nav-link scapp-nav-link--spaced">ACCUEIL</a>
        <div class="scapp-dropdown scapp-nav-dropdown">
          <button type="button" class="scapp-dropdown-toggle">STOCK ▾</button>
          <div class="scapp-dropdown-menu">
            <a href="stock.html" target="_blank" rel="noopener noreferrer" class="scapp-dropdown-item">RECHERCHE STOCK</a>
            <a href="stock_detailed.html" target="_blank" rel="noopener noreferrer" class="scapp-dropdown-item">STOCK DÉTAILLÉ</a>
            <a href="stock_hyper_detaille.html" target="_blank" rel="noopener noreferrer" class="scapp-dropdown-item">STOCK HYPER DÉTAILLÉ</a>
            <a href="stock_map.html" target="_blank" rel="noopener noreferrer" class="scapp-dropdown-item">LOCALISATION STOCK</a>
          </div>
        </div>

        <div class="scapp-dropdown scapp-nav-dropdown">
          <button type="button" class="scapp-dropdown-toggle">RÉFÉRENTIEL ARTICLE ▾</button>
          <div class="scapp-dropdown-menu scapp-dropdown-menu--wide">
            <a href="items.html" target="_blank" rel="noopener noreferrer" class="scapp-dropdown-item">CONSULTATION ARTICLE</a>
            <a href="article_request.html?v=3" target="_blank" rel="noopener noreferrer" class="scapp-dropdown-item">DEMANDE CRÉATION / MODIFICATION ARTICLE</a>
          </div>
        </div>

        <div class="scapp-dropdown scapp-nav-dropdown" >
          <button type="button" class="scapp-dropdown-toggle">PR & MAGASINS ▾</button>
          <div class="scapp-dropdown-menu scapp-dropdown-menu--xwide">
            <a href="technician.html" target="_blank" rel="noopener noreferrer" class="scapp-dropdown-item">CONSULTATION MAGASIN</a>
            <a href="stores.html" target="_blank" rel="noopener noreferrer" class="scapp-dropdown-item">RECHERCHE PR ET MAGASINS PROCHES D'UNE ADRESSE</a>
            <a href="technician_assignments.html" target="_blank" rel="noopener noreferrer" class="scapp-dropdown-item">CONSULTATION PR TECHNICIEN</a>
            <a href="pudo_directory.html" target="_blank" rel="noopener noreferrer" class="scapp-dropdown-item">ANNUAIRE POINTS RELAIS</a>
          </div>
        </div>

        <div class="scapp-dropdown scapp-nav-dropdown">
          <button type="button" class="scapp-dropdown-toggle">HELIOS ▾</button>
          <div class="scapp-dropdown-menu">
            <a href="helios.html" target="_blank" rel="noopener noreferrer" class="scapp-dropdown-item">PARC HELIOS</a>
          </div>
        </div>

        <div class="scapp-dropdown scapp-nav-dropdown">
          <button type="button" class="scapp-dropdown-toggle">CONSOMMABLE ▾</button>
          <div class="scapp-dropdown-menu">
            <a href="catalogue_consommables.html" target="_blank" rel="noopener noreferrer" class="scapp-dropdown-item">CATALOGUE CONSOMMABLES</a>
          </div>
        </div>

        <div class="scapp-dropdown scapp-nav-dropdown">
          <button type="button" class="scapp-dropdown-toggle">APPLICATIONS / OUTILS ▾</button>
          <div class="scapp-dropdown-menu">
            <a href="ol_mode_degrade_v2.html" target="_blank" rel="noopener noreferrer" class="scapp-dropdown-item">OL MODE DÉGRADÉ</a>
            <a href="downloads.html" target="_blank" rel="noopener noreferrer" class="scapp-dropdown-item">TÉLÉCHARGEMENTS</a>
          </div>
        </div>

        <div class="scapp-dropdown scapp-nav-dropdown" data-admin="1">
          <button type="button" class="scapp-dropdown-toggle">ADMINISTRATION ▾</button>
          <div class="scapp-dropdown-menu">
            <a href="treatments.html" target="_blank" rel="noopener noreferrer" class="scapp-dropdown-item">TRAITEMENTS</a>
            <a href="technician_admin.html" target="_blank" rel="noopener noreferrer" class="scapp-dropdown-item">ADMINISTRATION PR</a>
          </div>
        </div>

        ${llmRagLink}
      </nav>
      <div id="scapp-update-banner" class="scapp-update-banner"></div>
      <div class="scapp-header-actions">
        <button id="theme-toggle" type="button" class="btn-theme-toggle">Mode sombre</button>
        <button id="scapp-exit" type="button" class="btn-danger" title="Fermer l'application (arrête les serveurs locaux)">Quitter</button>
      </div>
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

    const adminKey = "scapp_admin_unlocked";
    const adminPassword = "12344321";
    const isAdminMenu = (dd.getAttribute("data-admin") || "") === "1";

    const isUnlocked = () => {
      if (!isAdminMenu) return true;
      try {
        // Persist across tabs/windows
        return localStorage.getItem(adminKey) === "1";
      } catch (e) {
        return false;
      }
    };

    const unlock = () => {
      if (!isAdminMenu) return true;
      if (isUnlocked()) return true;
      const val = prompt("Mot de passe Administration :");
      if ((val || "").trim() !== adminPassword) {
        alert("Mot de passe incorrect.");
        return false;
      }
      try {
        localStorage.setItem(adminKey, "1");
      } catch (e) {
      }
      return true;
    };

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
      if (!unlock()) return;
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
  scappInitExitListener();
  scappRenderHeader().then(() => {
    scappInitExitButton();
    scappStartHeartbeat();
  }).catch(() => {
    // ignore
  });
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
