document.addEventListener('DOMContentLoaded', () => {
  const path = window.location.pathname;

  // Détermine le préfixe selon la profondeur du fichier HTML
  let prefix = '';
  if (path.includes('/editions/')) {
    // Cas d'une page profonde comme /editions/britannicus/html/...
    prefix = '../../../';
  } else if (path.split('/').length > 3) {
    // Cas général pour des sous-dossiers
    prefix = '../'.repeat(path.split('/').length - 3);
  }

  // Insère le contenu du header
  document.getElementById('header').innerHTML = `
    <div class="logo-container">
      <img src="${prefix}assets/bandeau.png" alt="Frontispice de Bérénice" class="logo-main">
    </div>
  `;
});
