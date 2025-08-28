const input = document.getElementById('search-input');
const tbody = document.getElementById('results-body');
const fullTable = document.getElementById('full-table');
const filteredTable = document.getElementById('filtered-table');
const resultCount = document.getElementById('result-count');
const spinner = document.getElementById('spinner');

let timer;

// 🔐 Fonction pour échapper les caractères HTML
function escapeHTML(str) {
  return str.replace(/[&<>"']/g, function (char) {
    const escapeMap = {
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#039;',
    };
    return escapeMap[char];
  });
}

// 🔁 Fonction sécurisée pour afficher le tableau
function renderTable(data) {
  resultCount.textContent = `Résultats trouvés : ${data.length}`;

  if (data.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="7" style="text-align:center; color:#666;">
          Aucun résultat trouvé
        </td>
      </tr>`;
    return;
  }

  tbody.innerHTML = data.map(com => `
    <tr>
      <td>${escapeHTML(r.id.toString())}</td>
      <td>${escapeHTML(r.prenom || '')}</td>
      <td>${escapeHTML(r.nom || '')}</td>
      <td>${escapeHTML(r.address || '')}</td>
      <td>${escapeHTML(r.tel || '')}</td>
      <td>${escapeHTML(r.total || '')}</td>
      <td>${escapeHTML(r.created_at || '')}</td>
      <td>
        <a href="/edit/${escapeHTML(r.id.toString())}" class="button">Modifier</a>
        <a href="/delete/${escapeHTML(r.id.toString())}" class="button danger"
           onclick="return confirm('Vous voulez vraiment supprimer ?')">
           Supprimer
        </a>
      </td>
    </tr>
  `).join('');
}

// 🔍 Recherche dynamique avec fallback
input.addEventListener('input', () => {
  clearTimeout(timer);

  timer = setTimeout(() => {
    const q = input.value.trim();

    if (q.length < 1) {
      fullTable.style.display = "table";
      filteredTable.style.display = "none";
      resultCount.textContent = "";
      renderTable(initialData);
      return;
    }

    spinner.style.display = "block";// 👈 Affiche le spinner
    console.log(spinner); // 👀 Vérifie qu’il n’est pas null

    fetch(`/admin/search?ajax=1&q=${encodeURIComponent(q)}`)
      .then(resp => resp.json())
      .then(data => {
        spinner.style.display = "none";// 👈 Cache le spinner
        fullTable.style.display = "none";
        filteredTable.style.display = "table";
        renderTable(data);
      })
      .catch(err => {
        console.error("Erreur de recherche :", err);
        tbody.innerHTML = `
          <tr>
            <td colspan="7" style="text-align:center; color:red;">
              Une erreur est survenue lors de la recherche
            </td>
          </tr>`;
      });
  }, 300);
});

// 🟢 Affichage initial au chargement
renderTable(initialData);
