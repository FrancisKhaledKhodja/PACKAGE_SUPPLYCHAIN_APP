document.addEventListener("DOMContentLoaded", () => {
  const input = document.getElementById("rag-question");
  const modelInput = document.getElementById("ollama-model");
  const timeoutInput = document.getElementById("ollama-timeout");
  const btnAsk = document.getElementById("btn-ask");
  const btnGen = document.getElementById("btn-generate");
  const btnExec = document.getElementById("btn-execute");
  const status = document.getElementById("rag-status");
  const answer = document.getElementById("rag-answer");
  const debug = document.getElementById("rag-debug");
  const code = document.getElementById("polars-code");
  const preview = document.getElementById("preview-table");

  let lastPlan = null;

  function setStatus(txt) {
    if (status) status.textContent = txt || "";
  }

  function renderPreview(rows) {
    if (!preview) return;
    preview.innerHTML = "";
    if (!rows || !rows.length) {
      preview.textContent = "Aucune ligne.";
      return;
    }

    const table = document.createElement("table");
    table.style.width = "100%";
    table.style.borderCollapse = "collapse";

    const cols = Object.keys(rows[0] || {});

    const thead = document.createElement("thead");
    const trh = document.createElement("tr");
    cols.forEach((c) => {
      const th = document.createElement("th");
      th.textContent = c;
      th.style.borderBottom = "1px solid #ddd";
      th.style.textAlign = "left";
      th.style.padding = "0.35rem";
      trh.appendChild(th);
    });
    thead.appendChild(trh);
    table.appendChild(thead);

    const tbody = document.createElement("tbody");
    rows.forEach((r) => {
      const tr = document.createElement("tr");
      cols.forEach((c) => {
        const td = document.createElement("td");
        const v = r[c];
        td.textContent = v === null || v === undefined ? "" : String(v);
        td.style.borderBottom = "1px solid #f0f0f0";
        td.style.padding = "0.35rem";
        tr.appendChild(td);
      });
      tbody.appendChild(tr);
    });
    table.appendChild(tbody);

    preview.appendChild(table);
  }

  async function postJson(path, body) {
    const res = await fetch(API(path), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify(body || {}),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      throw new Error((data && (data.detail || data.error)) || "http_error");
    }
    return data;
  }

  async function handleAsk() {
    const q = (input && input.value ? input.value : "").trim();
    if (!q) {
      setStatus("Merci de saisir une question.");
      return;
    }
    setStatus("Interrogation LLM + RAG...");
    if (answer) answer.textContent = "";
    if (debug) debug.textContent = "";

    try {
      const ollamaModel = modelInput && modelInput.value ? modelInput.value.trim() : "";
      const ollamaTimeout = timeoutInput && timeoutInput.value ? Number(timeoutInput.value) : null;
      const data = await postJson("/assistant/llm_rag", {
        question: q,
        preview_rows: 200,
        top_k: 12,
        top_k_prompt: 8,
        embedding_model: "hash",
        ollama_model: ollamaModel || null,
        ollama_timeout_s: Number.isFinite(ollamaTimeout) ? ollamaTimeout : null,
      });

      if (answer) answer.textContent = data.answer || "";
      if (code) code.textContent = data.polars_code || "";
      if (debug) debug.textContent = JSON.stringify({ rag: data.rag, plan: data.plan }, null, 2);
      lastPlan = data.plan || null;
      setStatus("OK");
    } catch (e) {
      setStatus("Erreur: " + (e && e.message ? e.message : "inconnue"));
    }
  }

  async function handleGenerate() {
    const q = (input && input.value ? input.value : "").trim();
    if (!q) {
      setStatus("Merci de saisir une question.");
      return;
    }
    setStatus("Génération Polars via RAG...");
    try {
      const ollamaModel = modelInput && modelInput.value ? modelInput.value.trim() : "";
      const ollamaTimeout = timeoutInput && timeoutInput.value ? Number(timeoutInput.value) : null;
      const data = await postJson("/assistant/polars/generate", {
        question: q,
        preview_rows: 200,
        top_k: 12,
        embedding_model: "hash",
        ollama_model: ollamaModel || null,
        ollama_timeout_s: Number.isFinite(ollamaTimeout) ? ollamaTimeout : null,
      });
      if (code) code.textContent = data.polars_code || "";
      if (debug) debug.textContent = JSON.stringify({ rag: data.rag, plan: data.plan }, null, 2);
      lastPlan = data.plan || null;
      setStatus("OK");
    } catch (e) {
      setStatus("Erreur: " + (e && e.message ? e.message : "inconnue"));
    }
  }

  async function handleExecute() {
    if (!lastPlan) {
      setStatus("Génère d'abord un plan (bouton Générer Polars ou Interroger). ");
      return;
    }
    setStatus("Exécution preview (200 lignes max)...");
    try {
      const data = await postJson("/assistant/polars/execute", {
        plan: lastPlan,
        preview_rows: 200,
      });
      renderPreview(data.rows || []);
      setStatus("OK");
    } catch (e) {
      setStatus("Erreur: " + (e && e.message ? e.message : "inconnue"));
    }
  }

  if (btnAsk) btnAsk.addEventListener("click", handleAsk);
  if (btnGen) btnGen.addEventListener("click", handleGenerate);
  if (btnExec) btnExec.addEventListener("click", handleExecute);

  if (input) {
    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        handleAsk();
      }
    });
  }
});
