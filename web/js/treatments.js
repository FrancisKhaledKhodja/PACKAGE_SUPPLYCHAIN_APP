(function(){
  const statusEl = document.getElementById('treatments-status');
  const summaryEl = document.getElementById('treatments-summary');
  const outEl = document.getElementById('treatments-output');
  let __pollTimer = null;
  let __lastLogText = '';
  let __startedAt = null;

  const btnAll = document.getElementById('btn-run-all');

  function setButtonsDisabled(disabled){
    const btns = [btnAll].filter(Boolean);
    btns.forEach(b => { try { b.disabled = !!disabled; } catch(e) {} });
  }

  function setStatus(msg){
    if (statusEl) statusEl.textContent = msg;
  }

  function setSummary(html){
    if (!summaryEl) return;
    summaryEl.innerHTML = html || '';
  }

  function fmtTime(d){
    try {
      return new Date(d).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    } catch (e) {
      return '';
    }
  }

  function fmtDuration(ms){
    const s = Math.max(0, Math.round((ms || 0) / 1000));
    const m = Math.floor(s / 60);
    const r = s % 60;
    if (m <= 0) return `${r}s`;
    return `${m}min ${String(r).padStart(2, '0')}s`;
  }

  function appendOut(line){
    if (!outEl) return;
    outEl.textContent = (outEl.textContent || '') + (line || '') + "\n";
  }

  function clearOut(){
    if (outEl) outEl.textContent = '';
  }

  function setOutTextLimited(text){
    if (!outEl) return;
    const raw = String(text || '');
    const lines = raw.split(/\r?\n/);
    const maxLines = 60;
    const slice = lines.length > maxLines ? lines.slice(-maxLines) : lines;
    outEl.textContent = slice.join('\n');
  }

  function stopLogPolling(){
    if (__pollTimer) {
      clearInterval(__pollTimer);
      __pollTimer = null;
    }
  }

  async function readLogsText(){
    try {
      const res = await fetch(API('/pudo/logs?n=200'), {
        method: 'GET',
        credentials: 'include',
      });
      if (!res.ok) return '';
      const data = await res.json().catch(() => ({}));
      const lines = Array.isArray(data.lines) ? data.lines : [];
      return lines.join('\n');
    } catch (e) {
      return '';
    }
  }

  async function pollLogsOnce(){
    try {
      const res = await fetch(API('/pudo/logs?n=200'), {
        method: 'GET',
        credentials: 'include',
      });
      if (!res.ok) return;
      const data = await res.json().catch(() => ({}));
      const lines = Array.isArray(data.lines) ? data.lines : [];
      const text = lines.join('\n');
      if (!text) return;

      if (!__lastLogText) {
        __lastLogText = text;
        clearOut();
        setOutTextLimited(text);
        return;
      }

      if (text === __lastLogText) return;

      // Append only the delta if possible; fallback to replace.
      if (text.startsWith(__lastLogText)) {
        const delta = text.slice(__lastLogText.length);
        __lastLogText = text;
        if (delta.trim()) {
          // keep output short & readable
          setOutTextLimited(text);
        }
      } else {
        __lastLogText = text;
        clearOut();
        setOutTextLimited(text);
      }
    } catch (e) {
      // ignore polling errors
    }
  }

  async function runTreatment(name){
    stopLogPolling();
    __lastLogText = '';
    __startedAt = new Date();
    clearOut();
    setStatus('Traitement en cours...');
    setSummary(
      `<div><b>Début</b> : ${fmtTime(__startedAt)}</div>` +
      `<div class="muted" style="margin-top:0.25rem;">Vous pouvez ouvrir “Détails (logs)” si besoin.</div>`
    );

    // Baseline: ignore historical logs; only show new logs produced after this click.
    const baseline = await readLogsText();
    __lastLogText = baseline || '';

    setButtonsDisabled(true);

    // Start log polling while treatment runs
    __pollTimer = setInterval(pollLogsOnce, 1000);
    pollLogsOnce();

    try {
      const res = await fetch(API('/treatments/run'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ name }),
      });


      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        const endedAt = new Date();
        setStatus('Terminé avec erreur');
        setSummary(
          `<div><b>Début</b> : ${fmtTime(__startedAt)}</div>` +
          `<div><b>Fin</b> : ${fmtTime(endedAt)}</div>` +
          `<div><b>Durée</b> : ${fmtDuration(endedAt - __startedAt)}</div>`
        );
        stopLogPolling();
        await pollLogsOnce();
        appendOut('\n---\nRésumé erreur (API):\n' + JSON.stringify(data, null, 2));
        setButtonsDisabled(false);
        return;
      }

      const endedAt = new Date();
      setStatus('Terminé sans erreur');
      setSummary(
        `<div><b>Début</b> : ${fmtTime(__startedAt)}</div>` +
        `<div><b>Fin</b> : ${fmtTime(endedAt)}</div>` +
        `<div><b>Durée</b> : ${fmtDuration(endedAt - __startedAt)}</div>`
      );
      stopLogPolling();
      await pollLogsOnce();
      appendOut('\n---\nRésumé (API):\n' + JSON.stringify(data, null, 2));
      setButtonsDisabled(false);
    } catch (e) {
      const endedAt = new Date();
      setStatus('Terminé avec erreur');
      setSummary(
        `<div><b>Début</b> : ${fmtTime(__startedAt)}</div>` +
        `<div><b>Fin</b> : ${fmtTime(endedAt)}</div>` +
        `<div><b>Durée</b> : ${fmtDuration(endedAt - __startedAt)}</div>`
      );
      stopLogPolling();
      appendOut(String(e && e.message ? e.message : e));
      setButtonsDisabled(false);
    }
  }

  if (btnAll) btnAll.addEventListener('click', () => runTreatment('all'));
})();
