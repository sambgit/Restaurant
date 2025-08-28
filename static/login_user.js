        /*
 * AuthFlow Login System
 * Created by: TheDoc
 * Features: Modern login/register with animations
 * TheDoc's masterpiece
 */

// -------- Tab Switching --------
document.addEventListener('DOMContentLoaded', function() {
  const tabBtns = document.querySelectorAll('.tab-btn');
  const formContainers = document.querySelectorAll('.form-container');
  const tabSwitcher = document.querySelector('.tab-switcher');

  // -------- Switch manuel par clic --------
  tabBtns.forEach(btn => {
    btn.addEventListener('click', function() {
      activateTab(this.getAttribute('data-tab'));
    });
  });

  // -------- Fonction utilitaire --------
  function activateTab(tabName) {
    tabBtns.forEach(tab => tab.classList.remove('active'));
    formContainers.forEach(form => form.classList.remove('active'));

    const targetBtn = document.querySelector(`.tab-btn[data-tab="${tabName}"]`);
    if (targetBtn) targetBtn.classList.add('active');

    const targetForm = document.getElementById(tabName + '-form');
    if (targetForm) targetForm.classList.add('active');

    if (tabName === 'register') {
      tabSwitcher && tabSwitcher.classList.add('register-active');
    } else {
      tabSwitcher && tabSwitcher.classList.remove('register-active');
    }
  }

  // -------- Switch auto via URL --------
  const params = new URLSearchParams(window.location.search);
  const tabParam = params.get('tab');
  if (tabParam) {
  showModal('error', 'Veuillez créer un compte');
    activateTab(tabParam); // ex: tab=register → ouvre l’onglet inscription
  }

  // Password strength init
  const registerPassword = document.getElementById('registerPassword');
  if (registerPassword) {
    registerPassword.addEventListener('input', checkPasswordStrength);
  }

  // Form submissions
  const loginForm = document.getElementById('loginForm');
  if (loginForm) loginForm.addEventListener('submit', handleLogin);

  const registerForm = document.getElementById('registerForm');
  if (registerForm) registerForm.addEventListener('submit', handleRegister);

  console.log("AuthFlow initialized (API mode)");
});

// -------- Password Visibility --------
function togglePassword(inputId) {
  const passwordInput = document.getElementById(inputId);
  if (!passwordInput) return;
  const toggleIcon = passwordInput.parentElement.querySelector('.toggle-password i');
  if (!toggleIcon) return;

  if (passwordInput.type === 'password') {
    passwordInput.type = 'text';
    toggleIcon.classList.remove('fa-eye');
    toggleIcon.classList.add('fa-eye-slash');
  } else {
    passwordInput.type = 'password';
    toggleIcon.classList.remove('fa-eye-slash');
    toggleIcon.classList.add('fa-eye');
  }
}

// -------- Password Strength --------
function checkPasswordStrength() {
  const password = document.getElementById('registerPassword')?.value || '';
  const strengthBar = document.getElementById('strengthBar');
  const strengthText = document.getElementById('strengthText');
  if (!strengthBar || !strengthText) return;

  let strength = 0;
  if (password.length >= 8) strength += 1;
  if (/[a-z]/.test(password)) strength += 1;
  if (/[A-Z]/.test(password)) strength += 1;
  if (/[0-9]/.test(password)) strength += 1;
  if (/[^a-zA-Z0-9]/.test(password)) strength += 1;

  const strengthPercentage = (strength / 5) * 100;
  strengthBar.style.width = strengthPercentage + '%';

  let feedback = 'Very weak';
  let color = '#dc3545';
  if (strength === 2) { feedback = 'Weak'; color = '#fd7e14'; }
  if (strength === 3) { feedback = 'Fair'; color = '#ffc107'; }
  if (strength === 4) { feedback = 'Strong'; color = '#198754'; }
  if (strength === 5) { feedback = 'Very strong'; color = '#20c997'; }

  strengthBar.style.background = color;
  strengthText.textContent = feedback;
}

// -------- Register (API) --------
async function handleRegister(event) {
  event.preventDefault();

  const username = document.getElementById('registerName')?.value.trim();
  const email = document.getElementById('registerEmail')?.value.trim();
  const password = document.getElementById('registerPassword')?.value;
  const confirmPassword = document.getElementById('confirmPassword').value;
  const acceptTermsChecked  = document.getElementById('acceptTerms').checked;

  if (!username || !email || !password || !confirmPassword) {
    showModal('error', 'Erreur', 'Veuillez remplir tous les champs.');
    return;
  }
  if (password !== confirmPassword) {
    showModal('error', 'Erreur', 'Les mots de passe ne correspondent pas.');
    return;
  }
  if (!acceptTerms) {
    showModal('error', 'Erreur', 'Veuillez accepter les conditions.');
    return;
  }

  const submitBtn = event.target.querySelector('.auth-btn');
  submitBtn && submitBtn.classList.add('loading');
  if (submitBtn) submitBtn.disabled = true;

  try {

    const formData = new FormData();
    formData.append('username', username);
    formData.append('email', email);
    formData.append('password', password);
    // Si ton backend attend aussi confirm_password / acceptTerms, ajoute-les:
    formData.append('confirm_password', confirmPassword);
    formData.append('acceptTerms', acceptTermsChecked ? 'on' : '');

    const response = await fetch('/register', {
      method: 'POST',
      body: formData,
      // credentials: 'same-origin' // utile si tu relies une session/cookie
    });

    if (!response.ok) {
      const text = await response.text();
      throw new Error(text || 'Erreur lors de l’inscription.');
    }

    showModal('success', 'Compte créé', 'Vous pouvez maintenant vous connecter.');
    setTimeout(() => {
      document.querySelector('[data-tab="login"]')?.click();
      const loginEmail = document.getElementById('loginEmail');
      if (loginEmail) loginEmail.value = email;
    }, 1200);
  } catch (err) {
    showModal('error', 'Erreur', err.message);
  } finally {
    submitBtn && submitBtn.classList.remove('loading');
    if (submitBtn) submitBtn.disabled = false;
  }
}

// -------- Login (API) --------
async function handleLogin(event) {
  event.preventDefault();

  const email = document.getElementById('loginEmail')?.value.trim();
  const password = document.getElementById('loginPassword')?.value;
  const rememberMe = document.getElementById('rememberMe')?.checked;

  if (!email || !password) {
    showModal('error', 'Erreur', 'Veuillez remplir tous les champs.');
    return;
  }

  const submitBtn = event.target.querySelector('.auth-btn');
  submitBtn && submitBtn.classList.add('loading');
  if (submitBtn) submitBtn.disabled = true;

  try {
    const formData = new FormData();
    formData.append('email', email);
    formData.append('password', password);

    const response = await fetch('/login', {
      method: 'POST',
      body: formData,
      // credentials: 'same-origin'
    });

    if (!response.ok) {
      const text = await response.text();
      throw new Error(text || 'Identifiants invalides.');
    }

    if (rememberMe) {
      localStorage.setItem('userLoggedIn', 'true');
      localStorage.setItem('userEmail', email);
    }

    showModal('success', 'Connexion réussie', 'Bienvenue !');
    setTimeout(() => {
      window.location.href = '/dashboard';
    }, 1000);
  } catch (err) {
    showModal('error', 'Erreur', err.message);
  } finally {
    submitBtn && submitBtn.classList.remove('loading');
    if (submitBtn) submitBtn.disabled = false;
  }
}

// -------- Modals --------
function showModal(type, title, message) {
  const modal = document.getElementById(type + 'Modal');
  if (!modal) {
    alert(title + ' - ' + message); // fallback
    return;
  }
  const modalTitle = modal.querySelector('.modal-header h3');
  const modalMessage = modal.querySelector('.modal-body p');
  if (modalTitle) modalTitle.textContent = title;
  if (modalMessage) modalMessage.textContent = message;
  modal.style.display = 'block';

  if (type === 'success') {
    setTimeout(() => closeModal(), 3000);
  }
}

function closeModal() {
  const success = document.getElementById('successModal');
  const error = document.getElementById('errorModal');
  if (success) success.style.display = 'none';
  if (error) error.style.display = 'none';
}

window.addEventListener('click', function(event) {
  const success = document.getElementById('successModal');
  const error = document.getElementById('errorModal');
  if (event.target === success) success.style.display = 'none';
  if (event.target === error) error.style.display = 'none';
});

// -------- Social placeholders (conservent l’UI sans bloquer) --------
function signInWithGoogle() {
  console.log('Google Sign-In clicked');
  showModal('success', 'Google Sign-in', 'Google integration is in development.');
}

document.addEventListener('DOMContentLoaded', function() {
  document.querySelectorAll('.social-btn.facebook').forEach(btn => {
    btn.addEventListener('click', () => {
      console.log('Facebook Sign-In clicked');
      showModal('success', 'Facebook Sign-in', 'Facebook integration is in development.');
    });
  });
  document.querySelectorAll('.social-btn.github').forEach(btn => {
    btn.addEventListener('click', () => {
      console.log('GitHub Sign-In clicked');
      showModal('success', 'GitHub Sign-in', 'GitHub integration is in development.');
    });
  });
});

// -------- Focus animations --------
document.addEventListener('DOMContentLoaded', function() {
  const inputs = document.querySelectorAll('input');
  inputs.forEach(input => {
    input.addEventListener('focus', function() {
      if (this.parentElement) this.parentElement.style.transform = 'scale(1.02)';
    });
    input.addEventListener('blur', function() {
      if (this.parentElement) this.parentElement.style.transform = 'scale(1)';
    });
  });
});

// -------- Keyboard helpers --------
document.addEventListener('keydown', function(event) {
  if (event.key === 'Escape') closeModal();
});

// -------- Network feedback --------
window.addEventListener('online', () => console.log('Connection restored'));
window.addEventListener('offline', () => showModal('error', 'Connection Error', 'No internet connection.'));

// -------- Signature --------
console.log('%cAuthFlow by TheDoc (API Mode)', 'color:#667eea;font-size:16px;font-weight:bold;');