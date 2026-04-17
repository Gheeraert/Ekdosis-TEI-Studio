const currentPath = window.location.pathname;
const pathParts = currentPath.split('/').filter(p => p !== '');

// On veut revenir à la racine du site (là où se trouve menu_pieces.json)
const depth = pathParts.length;
const prefix = '../'.repeat(depth);
const currentRelative = window.location.pathname.slice(prefix.length);

console.log('→ currentPath =', currentPath);
console.log('→ pathParts =', pathParts);
console.log('→ prefix =', prefix);
console.log('→ fetch path =', prefix + 'menu_pieces.json');

console.log('Chargement depuis :', prefix + 'menu_pieces.json');

console.log('→ currentPath =', window.location.pathname);
console.log('→ prefix =', prefix);
console.log('→ chemin fetch =', prefix + 'menu_pieces.json');

fetch('/menu_pieces.json')
  .then(response => response.json())
  .then(data => {
    const container = document.getElementById('menu-lateral');
    container.innerHTML = '';

    // ➕ Lien vers la page d'accueil
    const boutonAccueil = document.createElement('a');
    boutonAccueil.href = prefix + 'index.html';
    boutonAccueil.textContent = '← Théâtre de Racine';
    boutonAccueil.className = 'bouton-accueil';
    container.appendChild(boutonAccueil);

    const iconeAccueil = document.createElement('a');
    iconeAccueil.href = prefix + 'index.html';
    iconeAccueil.innerHTML = '🏠';
    iconeAccueil.className = 'icone-accueil';
    iconeAccueil.title = 'Retour à l’accueil';
    document.body.appendChild(iconeAccueil); // 🟡 attention : on l'ajoute au body, pas dans #menu-lateral

    // ➕ Titre fixe
    const titreNav = document.createElement('h2');
    titreNav.className = 'titre-navigation';
    titreNav.textContent = 'Navigation';
    container.appendChild(titreNav);

    // Récupérer les états ouverts depuis localStorage
    const openPieces = JSON.parse(localStorage.getItem('openPieces') || '{}');
    const openActes = JSON.parse(localStorage.getItem('openActes') || '{}');

    data.forEach(piece => {
      const title = document.createElement('button');
      title.className = 'piece-title';
      title.type = 'button';
      title.innerHTML = '\u25B6 ' + piece.titre;

      const pieceMenu = document.createElement('div');
      pieceMenu.className = 'sous-menu';
      pieceMenu.style.display = 'none';

      const pieceBase = piece.url.replace('index.html', '');
      const isCurrentPiece = currentRelative.startsWith(pieceBase) && currentRelative !== pieceBase; // Vérifie si l'URL courante appartient à cette pièce

      // Déterminer si la pièce doit être ouverte
      let shouldOpenPiece = openPieces[piece.titre] || isCurrentPiece;

      piece.actes.forEach(acte => {
        if (acte.scenes) {
          const acteTitle = document.createElement('button');
          acteTitle.className = 'acte-title';
          acteTitle.type = 'button';
          acteTitle.innerHTML = '\u25B6 ' + acte.label;

          const acteMenu = document.createElement('div');
          acteMenu.className = 'sous-sous-menu';
          acteMenu.style.display = 'none';

          const isCurrentActe = acte.scenes.some(scene => currentRelative === pieceBase + scene.file);

          // Déterminer si l'acte doit être ouvert
          const shouldOpenActe = openActes[piece.titre + '_' + acte.label] || isCurrentActe;

          if (shouldOpenActe) {
            acteMenu.style.display = 'block';
            acteTitle.innerHTML = '▼ ' + acte.label;
            shouldOpenPiece = true; // Si un acte est ouvert, la pièce doit aussi l'être
          }

          acte.scenes.forEach(scene => {
            const a = document.createElement('a');
            a.href = prefix + piece.url.replace('index.html', '') + scene.file;
            a.textContent = scene.label;
            // Ajoute une classe 'active' si c'est la page courante
            if (currentRelative === pieceBase + scene.file) {
              a.classList.add('active-menu-item');
            }
            acteMenu.appendChild(a);
          });

          acteTitle.addEventListener('click', () => {
            const open = acteMenu.style.display === 'block';
            acteMenu.style.display = open ? 'none' : 'block';
            acteTitle.innerHTML = (open ? '\u25B6' : '\u25BC') + ' ' + acte.label;

            // Mettre à jour l'état dans localStorage
            if (!open) {
              openActes[piece.titre + '_' + acte.label] = true;
            } else {
              delete openActes[piece.titre + '_' + acte.label];
            }
            localStorage.setItem('openActes', JSON.stringify(openActes));
          });

          pieceMenu.appendChild(acteTitle);
          pieceMenu.appendChild(acteMenu);
        }
      });

      title.addEventListener('click', () => {
        const isOpen = pieceMenu.style.display === 'block';
        pieceMenu.style.display = isOpen ? 'none' : 'block';
        title.innerHTML = (isOpen ? '\u25B6' : '\u25BC') + ' ' + piece.titre;

        // Mettre à jour l'état dans localStorage
        if (!isOpen) {
          openPieces[piece.titre] = true;
        } else {
          delete openPieces[piece.titre];
        }
        localStorage.setItem('openPieces', JSON.stringify(openPieces));
      });

      // Appliquer l'état déplié si nécessaire
      if (shouldOpenPiece) {
        pieceMenu.style.display = 'block';
        title.innerHTML = '▼ ' + piece.titre;
      }

      container.appendChild(title);
      container.appendChild(pieceMenu);
    });
  })
  .catch(err => {
    document.getElementById('menu-lateral').innerHTML = '<p style="color:red;">Erreur de chargement du menu</p>';
    console.error(err);
  });