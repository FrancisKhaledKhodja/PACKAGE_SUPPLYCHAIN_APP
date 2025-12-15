document.addEventListener("DOMContentLoaded", () => {
  const codeInput = document.getElementById("an-code");
  const form = document.getElementById("form-article-network");
  const btn = document.getElementById("an-btn-load");
  const statusDiv = document.getElementById("an-status");
  const container = document.getElementById("article-network");

  if (!form || !codeInput || !container) return;

  function getQueryParam(name) {
    const params = new URLSearchParams(window.location.search);
    return params.get(name) || "";
  }

  const initialCode = (getQueryParam("code") || "").trim();
  if (initialCode) {
    codeInput.value = initialCode.toUpperCase();
  }

  async function loadNetwork() {
    const raw = (codeInput.value || "").trim();
    const code = raw.toUpperCase();
    if (!code) {
      statusDiv.textContent = "Merci de saisir un code article.";
      return;
    }

    statusDiv.textContent = "Chargement du graphe...";

    try {
      const resp = await fetch(API(`/items/${encodeURIComponent(code)}/network`), {
        method: "GET",
        credentials: "include",
      });
      if (!resp.ok) {
        statusDiv.textContent = `Erreur API (${resp.status})`;
        return;
      }
      const data = await resp.json();
      const nodesData = data.nodes || [];
      const edgesData = data.edges || [];

      if (!nodesData.length) {
        statusDiv.textContent = "Aucune relation trouvée pour ce code article.";
        container.innerHTML = "";
        return;
      }

      const visNodes = new vis.DataSet(nodesData.map((n) => ({
        id: n.id,
        label: n.label,
        group: n.group || (n.id === code ? "root" : "item"),
      })));

      const visEdges = new vis.DataSet(edgesData.map((e) => {
        const base = {
          from: e.from,
          to: e.to,
        };
        if (e.type === "equiv") {
          return {
            ...base,
            color: { color: "#22c55e" },
            dashes: true,
          };
        }
        if (e.type === "bom") {
          return {
            ...base,
            color: { color: "#3b82f6" },
            arrows: "to",
          };
        }
        return base;
      }));

      const options = {
        nodes: {
          shape: "dot",
          size: 14,
          font: { size: 14 },
        },
        groups: {
          root: {
            color: { background: "#f97316", border: "#c2410c" },
            shape: "dot",
            size: 18,
          },
          equiv: {
            color: { background: "#22c55e", border: "#15803d" },
          },
          item: {
            color: { background: "#60a5fa", border: "#1d4ed8" },
          },
        },
        physics: {
          stabilization: true,
          barnesHut: {
            gravitationalConstant: -3000,
            springLength: 150,
          },
        },
        interaction: {
          hover: true,
          tooltipDelay: 100,
        },
      };

      container.innerHTML = "";
      const network = new vis.Network(container, { nodes: visNodes, edges: visEdges }, options);

      statusDiv.textContent = `${visNodes.length} nœud(s), ${visEdges.length} lien(s).`;

      network.on("click", (params) => {
        if (!params.nodes || !params.nodes.length) return;
        const nodeId = params.nodes[0];
        if (typeof nodeId === "string" && nodeId !== codeInput.value) {
          codeInput.value = nodeId;
        }
      });
    } catch (e) {
      statusDiv.textContent = "Erreur lors du chargement du graphe.";
    }
  }

  form.addEventListener("submit", (ev) => {
    ev.preventDefault();
    loadNetwork();
  });

  if (initialCode) {
    loadNetwork();
  }
});
