from __future__ import annotations

import html


def render_static_search_page(*, site_title: str) -> str:
    title = f"Recherche — {site_title}" if site_title else "Recherche"
    return f"""<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <style>
    :root {{
      color-scheme: light dark;
      --background: #f8f4ec;
      --surface: #fffaf2;
      --text: #241c18;
      --muted: #6f6258;
      --accent: #7b2d26;
      --border: #d9cbb8;
    }}
    @media (prefers-color-scheme: dark) {{
      :root {{
        --background: #171412;
        --surface: #211c19;
        --text: #f2e8dc;
        --muted: #cbbdad;
        --accent: #e8a39b;
        --border: #4f423a;
      }}
    }}
    body {{
      margin: 0;
      background: var(--background);
      color: var(--text);
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      line-height: 1.55;
    }}
    main {{
      max-width: 920px;
      margin: 0 auto;
      padding: 2rem 1rem 3rem;
    }}
    header {{
      margin-bottom: 1.5rem;
    }}
    h1 {{
      margin: 0 0 0.5rem;
      font-size: clamp(2rem, 5vw, 3rem);
    }}
    a {{
      color: var(--accent);
      text-underline-offset: 0.16em;
    }}
    .search-panel {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 1rem;
      padding: 1rem;
      box-shadow: 0 0.5rem 2rem rgba(0, 0, 0, 0.06);
    }}
    label {{
      display: block;
      font-weight: 700;
      margin-bottom: 0.35rem;
    }}
    input[type="search"] {{
      box-sizing: border-box;
      width: 100%;
      border: 1px solid var(--border);
      border-radius: 0.7rem;
      padding: 0.75rem 0.9rem;
      font: inherit;
      background: var(--background);
      color: var(--text);
    }}
    .hint, .status {{
      color: var(--muted);
    }}
    .status {{
      margin: 1rem 0;
    }}
    .results {{
      list-style: none;
      padding: 0;
      margin: 1rem 0 0;
      display: grid;
      gap: 0.85rem;
    }}
    .result {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 1rem;
      padding: 1rem;
    }}
    .result-title {{
      font-weight: 700;
      margin-bottom: 0.25rem;
    }}
    .speaker {{
      color: var(--muted);
      font-variant: small-caps;
      letter-spacing: 0.04em;
      margin: 0.25rem 0;
    }}
    .verse {{
      margin: 0.45rem 0 0.7rem;
    }}
    .links {{
      display: flex;
      flex-wrap: wrap;
      gap: 0.4rem 0.8rem;
      font-size: 0.95rem;
    }}
  </style>
</head>
<body>
<main>
  <header>
    <h1>Recherche</h1>
    <p>Cette page interroge un index statique local généré avec le site publié.</p>
    <p class="hint">Les liens DTS vers les fragments TEI apparaissent seulement si l’export DTS a également été activé.</p>
  </header>
  <section class="search-panel" aria-labelledby="search-label">
    <label id="search-label" for="search-input">Rechercher dans les vers</label>
    <input id="search-input" type="search" autocomplete="off" placeholder="Texte, locuteur, pièce, acte ou scène">
    <p id="search-status" class="status" role="status">Chargement de l’index…</p>
  </section>
  <ol id="search-results" class="results"></ol>
</main>
<script>
(() => {{
  const INDEX_URL = 'search/index.json';
  const input = document.getElementById('search-input');
  const status = document.getElementById('search-status');
  const results = document.getElementById('search-results');
  let entries = [];

  function normalize(value) {{
    return String(value || '')
      .normalize('NFD')
      .replace(/[\\u0300-\\u036f]/g, '')
      .toLocaleLowerCase('fr');
  }}

  function appendText(parent, className, text) {{
    if (!text) return null;
    const node = document.createElement('p');
    node.className = className;
    node.textContent = text;
    parent.appendChild(node);
    return node;
  }}

  function appendLink(parent, href, label) {{
    if (!href) return;
    const link = document.createElement('a');
    link.href = href;
    link.textContent = label;
    parent.appendChild(link);
  }}

  function renderResult(entry) {{
    const item = document.createElement('li');
    item.className = 'result';

    const title = document.createElement('div');
    title.className = 'result-title';
    title.textContent = `${{entry.piece || 'Pièce sans titre'}} — ${{entry.label || entry.ref || 'référence'}}`;
    item.appendChild(title);

    appendText(item, 'speaker', entry.speaker);
    appendText(item, 'verse', entry.text);

    const links = document.createElement('div');
    links.className = 'links';
    appendLink(links, entry.html, 'Lire dans le site');
    appendLink(links, entry.dts_document, 'Fragment TEI');
    appendLink(links, entry.dts_navigation, 'Navigation DTS');
    item.appendChild(links);

    return item;
  }}

  function searchableText(entry) {{
    return normalize([entry.text, entry.speaker, entry.piece, entry.label].join(' '));
  }}

  function render() {{
    const query = normalize(input.value);
    results.replaceChildren();

    if (!entries.length) {{
      status.textContent = 'Index chargé, mais aucun vers indexable n’a été trouvé.';
      return;
    }}

    const matches = query
      ? entries.filter((entry) => searchableText(entry).includes(query))
      : entries.slice(0, 50);

    if (!matches.length) {{
      status.textContent = 'Aucun résultat ne correspond à cette recherche.';
      return;
    }}

    status.textContent = `${{matches.length}} résultat${{matches.length > 1 ? 's' : ''}}`;
    matches.forEach((entry) => results.appendChild(renderResult(entry)));
  }}

  fetch(INDEX_URL)
    .then((response) => {{
      if (!response.ok) throw new Error(`HTTP ${{response.status}}`);
      return response.json();
    }})
    .then((payload) => {{
      entries = Array.isArray(payload) ? payload : [];
      render();
    }})
    .catch((error) => {{
      status.textContent = `Impossible de charger l’index de recherche : ${{error.message}}.`;
    }});

  input.addEventListener('input', render);
}})();
</script>
</body>
</html>
"""


def render_static_search_head_assets() -> str:
    return """<style>
    .content-shell-search {
      padding: 0.55rem 0.1rem 2.5rem;
      max-width: 980px;
      background: transparent;
      border: none;
      box-shadow: none;
    }
    .search-content {
      margin: 0;
      color: var(--ink);
      font-family: var(--font-body);
    }
    .search-content > header,
    .search-panel,
    .result {
      background: var(--bg-panel);
      border: 1px solid var(--line);
      box-shadow: var(--shadow-soft);
    }
    .search-content > header {
      margin: 0 0 1rem;
      padding: 1rem 1.1rem;
    }
    .search-content h2 {
      margin: 0 0 0.45rem;
      font-size: clamp(1.8rem, 4vw, 2.55rem);
    }
    .search-content a {
      color: var(--accent);
    }
    .search-content a:hover {
      color: var(--accent-soft);
    }
    .search-panel {
      margin: 0 0 1rem;
      padding: 1rem 1.1rem;
    }
    .search-panel label {
      display: block;
      margin-bottom: 0.35rem;
      color: var(--ink);
      font-family: var(--font-ui);
      font-weight: 700;
    }
    .search-panel input[type="search"] {
      box-sizing: border-box;
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 0.6rem;
      padding: 0.7rem 0.85rem;
      background: var(--bg);
      color: var(--ink);
      font: inherit;
    }
    .search-panel input[type="search"]::placeholder {
      color: var(--ink-muted);
    }
    .search-hint,
    .search-status {
      color: var(--ink-muted);
      font-family: var(--font-ui);
      font-size: 0.94rem;
    }
    .search-status {
      margin: 0.85rem 0 0;
    }
    .search-results {
      list-style: none;
      padding: 0;
      margin: 1rem 0 0;
      display: grid;
      gap: 0.85rem;
    }
    .result {
      padding: 1rem 1.1rem;
    }
    .result-title {
      margin-bottom: 0.25rem;
      color: var(--ink);
      font-family: var(--font-ui);
      font-weight: 700;
    }
    .speaker {
      margin: 0.25rem 0;
      color: var(--ink-muted);
      font-variant: small-caps;
      letter-spacing: 0.04em;
    }
    .verse {
      margin: 0.45rem 0 0.7rem;
      color: var(--ink);
    }
    .links {
      display: flex;
      flex-wrap: wrap;
      gap: 0.4rem 0.8rem;
      font-family: var(--font-ui);
      font-size: 0.94rem;
    }
  </style>"""


def render_static_search_content() -> str:
    return """<article class="search-content" aria-labelledby="search-title">
  <header>
    <h2 id="search-title">Recherche</h2>
    <p>Cette page interroge un index statique local généré avec le site publié.</p>
    <p class="search-hint">Les liens DTS vers les fragments TEI apparaissent seulement si l’export DTS a également été activé.</p>
  </header>
  <section class="search-panel" aria-labelledby="search-label">
    <label id="search-label" for="search-input">Rechercher dans les vers</label>
    <input id="search-input" type="search" autocomplete="off" placeholder="Texte, locuteur, pièce, acte ou scène">
    <p id="search-status" class="search-status" role="status">Chargement de l’index…</p>
  </section>
  <ol id="search-results" class="search-results"></ol>
</article>"""


def render_static_search_script() -> str:
    return """<script>
(() => {
  const INDEX_URL = 'search/index.json';
  const input = document.getElementById('search-input');
  const status = document.getElementById('search-status');
  const results = document.getElementById('search-results');
  let entries = [];

  function normalize(value) {
    return String(value || '')
      .normalize('NFD')
      .replace(/[\\u0300-\\u036f]/g, '')
      .toLocaleLowerCase('fr');
  }

  function appendText(parent, className, text) {
    if (!text) return null;
    const node = document.createElement('p');
    node.className = className;
    node.textContent = text;
    parent.appendChild(node);
    return node;
  }

  function appendLink(parent, href, label) {
    if (!href) return;
    const link = document.createElement('a');
    link.href = href;
    link.textContent = label;
    parent.appendChild(link);
  }

  function renderResult(entry) {
    const item = document.createElement('li');
    item.className = 'result';

    const title = document.createElement('div');
    title.className = 'result-title';
    title.textContent = `${entry.piece || 'Pièce sans titre'} — ${entry.label || entry.ref || 'référence'}`;
    item.appendChild(title);

    appendText(item, 'speaker', entry.speaker);
    appendText(item, 'verse', entry.text);

    const links = document.createElement('div');
    links.className = 'links';
    appendLink(links, entry.html, 'Lire dans le site');
    appendLink(links, entry.dts_document, 'Fragment TEI');
    appendLink(links, entry.dts_navigation, 'Navigation DTS');
    item.appendChild(links);

    return item;
  }

  function searchableText(entry) {
    return normalize([entry.text, entry.speaker, entry.piece, entry.label].join(' '));
  }

  function render() {
    const query = normalize(input.value);
    results.replaceChildren();

    if (!entries.length) {
      status.textContent = 'Index chargé, mais aucun vers indexable n’a été trouvé.';
      return;
    }

    const matches = query
      ? entries.filter((entry) => searchableText(entry).includes(query))
      : entries.slice(0, 50);

    if (!matches.length) {
      status.textContent = 'Aucun résultat ne correspond à cette recherche.';
      return;
    }

    status.textContent = `${matches.length} résultat${matches.length > 1 ? 's' : ''}`;
    matches.forEach((entry) => results.appendChild(renderResult(entry)));
  }

  fetch(INDEX_URL)
    .then((response) => {
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return response.json();
    })
    .then((payload) => {
      entries = Array.isArray(payload) ? payload : [];
      render();
    })
    .catch((error) => {
      status.textContent = `Impossible de charger l’index de recherche : ${error.message}.`;
    });

  input.addEventListener('input', render);
})();
</script>"""


def render_static_search_page(*, site_title: str) -> str:
    title = f"Recherche — {site_title}" if site_title else "Recherche"
    return f"""<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  {render_static_search_head_assets()}
</head>
<body>
  <main>
    {render_static_search_content()}
  </main>
  {render_static_search_script()}
</body>
</html>
"""
