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

// 🧪 Données de test
let users = [
  { id: 1, username: "John" },
  { id: 2, username: "Jane" },
];

// 🔧 Éléments DOM
const userTable = document.getElementById("filtered-table").getElementsByTagName("tbody")[0];
const addUserBtn = document.getElementById("add-user-btn");
const addUserModal = document.getElementById("add-user-modal");
const closeModal = document.querySelector(".close");
const userForm = document.getElementById("user-form");

// 🔁 Affichage du tableau des menus
function renderUsers() {
  userTable.innerHTML = "";
  users.forEach((user) => {
    const row = userTable.insertRow();
    row.innerHTML = `
      <td>${escapeHTML(user.id.toString())}</td>
      <td>${escapeHTML(user.nom)}</td>
      <td>${escapeHTML(user.description)}</td>
      <td>${escapeHTML(user.prix.toString())}</td>
      <td>${escapeHTML(user.image)}</td>
      <td>${escapeHTML(user.categorie)}</td>
      <td>
        <button onclick="editUser(${user.id})">Modifier</button>
        <button onclick="deleteUser(${user.id})">Supprimer</button>
      </td>
    `;
  });
}

// ➕ Ajouter un utilisateur
addUserBtn.addEventListener("click", () => {
  addUserModal.style.display = "flex";
});

closeModal.addEventListener("click", () => {
  addUserModal.style.display = "none";
});

userForm.addEventListener("submit", (e) => {
  e.preventDefault();
  const username = document.getElementById("nom").value;

  const newUser = {
    id: users.length + 1,
    username: username,
  };

  users.push(newUser);
  renderUsers();
  addUserModal.style.display = "none";
  userForm.reset();
});

// ✏️ Modifier un menu
function editUser(id) {
  const user = users.find((user) => user.id === id);
  if (user) {
    document.getElementById("nom").value = user.nom;
    document.getElementById("description").value = user.description;
    document.getElementById("prix").value = user.prix;
    document.getElementById("image").value = user.image;
    document.getElementById("categorie").value = user.categorie;
    addUserModal.style.display = "flex";

    userForm.onsubmit = (e) => {
      e.preventDefault();
      user.nom = document.getElementById("nom").value;
      user.description = document.getElementById("description").value;
      user.prix = document.getElementById("prix").value;
      user.image = document.getElementById("image").value;
      user.categorie = document.getElementById("categorie").value;
      renderUsers();
      addUserModal.style.display = "none";
      userForm.reset();
    };
  }
}

// ❌ Supprimer un utilisateur
function deleteUser(id) {
  if (confirm("Voulez-vous vraiment supprimer cet utilisateur ?")) {
    users = users.filter((user) => user.id !== id);
    renderUsers();
  }
}
// 🟢 Rendu initial
renderUsers();
