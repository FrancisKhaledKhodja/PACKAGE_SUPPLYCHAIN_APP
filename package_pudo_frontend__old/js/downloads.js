(function(){
  const filesDiv = document.getElementById('files');

  function escapeHtml(s){
    return (s == null ? '' : String(s))
      .replace(/&/g,'&amp;')
      .replace(/</g,'&lt;')
      .replace(/>/g,'&gt;')
      .replace(/"/g,'&quot;')
      .replace(/'/g,'&#39;');
  }

  function render(summary){
    if (!summary){
      filesDiv.innerHTML = '<div class="muted">Aucun fichier détecté</div>';
      return;
    }

    const items = [
      { key: 'annuaire_pr', label: 'Annuaire PR', path: '/downloads/annuaire_pr' },
      // key chronopost_fusionne du résumé API mais endpoint de téléchargement /downloads/chronopost
      { key: 'chronopost_fusionne', label: 'Chronopost fusionné', path: '/downloads/chronopost' },
      { key: 'lm2s', label: 'LM2S', path: '/downloads/lm2s' },
      { key: 'carnet_chronopost', label: 'Carnet Chronopost', path: '/downloads/carnet_chronopost' },
      { key: 'stock_final_csv', label: 'Stock final (CSV UTF-8)', path: '/downloads/stock_final_csv' },
    ];

    const rows = items.map(it => {
      const info = summary[it.key] || {};
      const available = !!info.available;
      const filename = info.filename || '';
      const meta = available
        ? `<span class="muted">Dernier fichier : ${escapeHtml(filename)}</span><br/>`
        : '<span class="muted">Aucun fichier trouvé</span><br/>';
      const link = available
        ? `<a href="${API(it.path)}" class="btn" style="display:inline-block; margin-top:6px">Télécharger</a>`
        : '';
      return `<li style="margin:8px 0">
        <strong>${escapeHtml(it.label)}</strong><br/>
        ${meta}
        ${link}
      </li>`;
    }).join('');

    filesDiv.innerHTML = `<ul style="list-style:none; padding:0; margin:0">${rows}</ul>`;
  }

  fetch(API('/downloads/'))
    .then(r => r.json())
    .then(render)
    .catch(() => {
      filesDiv.textContent = 'Erreur de chargement';
    });
})();
