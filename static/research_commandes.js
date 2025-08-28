const input = document.getElementById('search-input');
const tbody = document.getElementById('results-body');
const fullTable = document.getElementById('full-table');
const filteredTable = document.getElementById('filtered-table');
const resultCount = document.getElementById('result-count');
let timer;

function escapeHTML(str) {
  return String(str).replace(/[&<>"']/g, char => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#039;',
  }[char]));
}

function renderTable(data) {
  resultCount.textContent = `Résultats trouvés : ${data.length}`;

  if (!data.length) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;color:#666;">Aucun résultat trouvé</td></tr>`;
    return;
  }

  tbody.innerHTML = data.map(com => `
    <tr>
      <td>${escapeHTML(com.id)}</td>
      <td>${escapeHTML(com.prenom)}</td>
      <td>${escapeHTML(com.nom)}</td>
      <td>${escapeHTML(com.adresse)}</td>
      <td>${escapeHTML(com.tel)}</td>
      <td>${escapeHTML(com.total)}</td>
      <td>${escapeHTML(com.created_at)}</td>
      <td>
        <a href="/edit/${escapeHTML(com.id)}" class="button">Modifier</a>
        <a href="/delete/${escapeHTML(com.id)}" class="button danger"
           onclick="return confirm('Vous voulez vraiment supprimer ?')">Supprimer</a>
      </td>
    </tr>
  `).join('');
}

input.addEventListener('input', () => {
  clearTimeout(timer);

  timer = setTimeout(() => {
    const n = input.value.trim();

    if (!n) {
      // Mode initial : recharge toutes les données
      filteredTable.style.display = "none";
      fullTable.style.display = "table";
      resultCount.textContent = "";
      return;
    }

    fetch(`/admin/search_commandes?ajax=1&n=${encodeURIComponent(n)}`)
      .then(resp => resp.json())
      .then(data => {
        fullTable.style.display = "none";
        filteredTable.style.display = "table";
        renderTable(data);
      })
      .catch(err => {
        console.error("Erreur de recherche :", err);
      });
  }, 300);
});
