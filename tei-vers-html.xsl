<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:tei="http://www.tei-c.org/ns/1.0"
  exclude-result-prefixes="tei">

  <xsl:output method="html" encoding="UTF-8" indent="yes"/>
  <xsl:key name="witness-by-id" match="tei:witness" use="@xml:id"/>

  <xsl:template name="format-witness-short">
   <xsl:param name="id"/>
   <xsl:variable name="witness-text" select="normalize-space(string(key('witness-by-id', $id)[1]))"/>
   <xsl:choose>
     <xsl:when test="$witness-text != '' and contains($witness-text, ')')">
      <xsl:value-of select="concat(substring-before($witness-text, ')'), ')')"/>
     </xsl:when>
     <xsl:when test="$witness-text != ''">
       <xsl:value-of select="$witness-text"/>
     </xsl:when>
     <xsl:otherwise>
      <xsl:value-of select="concat('#', $id)"/>
     </xsl:otherwise>
   </xsl:choose>
  </xsl:template>

<xsl:template name="format-wit-lines">
  <xsl:param name="wit"/>
  <xsl:param name="reading"/>

  <xsl:variable name="trim" select="normalize-space($wit)"/>
  
  <xsl:if test="$trim != ''">
    <xsl:variable name="first" select="substring-before(concat($trim, ' '), ' ')"/>
    <xsl:variable name="rest" select="normalize-space(substring-after($trim, ' '))"/>
    <xsl:variable name="id" select="substring-after($first, '#')"/>
  
    <xsl:call-template name="format-witness-short">
      <xsl:with-param name="id" select="$id"/>
    </xsl:call-template>
    <xsl:text>: </xsl:text>
    <xsl:value-of select="$reading"/>
    
    <xsl:if test="$rest != ''">
      <xsl:text>&#10;</xsl:text>
      <xsl:call-template name="format-wit-lines">
        <xsl:with-param name="wit" select="$rest"/>
        <xsl:with-param name="reading" select="$reading"/>
      </xsl:call-template>
    </xsl:if>
  </xsl:if>
</xsl:template>

<xsl:template name="normalize-wit-list">
  <xsl:param name="wit"/>
  <xsl:variable name="trim" select="normalize-space($wit)"/>
  <xsl:if test="$trim != ''">
    <xsl:variable name="first" select="substring-before(concat($trim, ' '), ' ')"/>
    <xsl:variable name="rest" select="normalize-space(substring-after($trim, ' '))"/>
    <xsl:choose>
      <xsl:when test="starts-with($first, '#')">
        <xsl:value-of select="substring-after($first, '#')"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:value-of select="$first"/>
      </xsl:otherwise>
    </xsl:choose>
    <xsl:if test="$rest != ''">
      <xsl:text> </xsl:text>
      <xsl:call-template name="normalize-wit-list">
        <xsl:with-param name="wit" select="$rest"/>
      </xsl:call-template>
    </xsl:if>
  </xsl:if>
</xsl:template>

<xsl:template name="app-variation-classes">
  <xsl:text>variation</xsl:text>
  <xsl:if test="normalize-space(tei:lem) = ''">
    <xsl:text> variation-empty</xsl:text>
  </xsl:if>
  <xsl:if test="@type = 'minor'">
    <xsl:text> variation-minor</xsl:text>
  </xsl:if>
  <xsl:if test="normalize-space(@ana) = '#punctuation_only' or (not(@ana) and @subtype = 'punctuation')">
    <xsl:text> variation-punctuation-only</xsl:text>
  </xsl:if>
  <xsl:if test="normalize-space(@ana) = '#case_only'">
    <xsl:text> variation-case-only</xsl:text>
  </xsl:if>
  <xsl:if test="normalize-space(@ana) = '#spacing_or_hyphen_only'">
    <xsl:text> variation-spacing-or-hyphen-only</xsl:text>
  </xsl:if>
  <xsl:if test="@subtype = 'mixed' or contains(normalize-space(@ana), '+')">
    <xsl:text> variation-mixed</xsl:text>
  </xsl:if>
</xsl:template>

<xsl:template name="app-tooltip-text">
  <xsl:for-each select="tei:rdg">
    <xsl:call-template name="format-wit-lines">
      <xsl:with-param name="wit" select="@wit"/>
      <xsl:with-param name="reading">
        <xsl:choose>
          <xsl:when test="normalize-space(.) != ''">
            <xsl:value-of select="normalize-space(.)"/>
          </xsl:when>
          <xsl:when test="@type = 'omission'">omission</xsl:when>
        </xsl:choose>
      </xsl:with-param>
    </xsl:call-template>
    <xsl:text>&#10;&#10;</xsl:text>
  </xsl:for-each>
</xsl:template>

<xsl:template name="render-app-reading">
  <xsl:param name="reading"/>
  <xsl:param name="kind"/>
  <xsl:param name="is-default" select="false()"/>
  <span>
    <xsl:attribute name="class">
      <xsl:text>app-reading</xsl:text>
      <xsl:if test="$is-default">
        <xsl:text> app-reading-default app-reading-active</xsl:text>
      </xsl:if>
    </xsl:attribute>
    <xsl:attribute name="data-kind">
      <xsl:value-of select="$kind"/>
    </xsl:attribute>
    <xsl:attribute name="data-wits">
      <xsl:call-template name="normalize-wit-list">
        <xsl:with-param name="wit" select="$reading/@wit"/>
      </xsl:call-template>
    </xsl:attribute>
    <xsl:if test="$reading/@type = 'omission'">
      <xsl:attribute name="data-omission">true</xsl:attribute>
    </xsl:if>
    <xsl:if test="not($is-default)">
      <xsl:attribute name="hidden">hidden</xsl:attribute>
    </xsl:if>
    <xsl:apply-templates select="$reading/node()"/>
  </span>
</xsl:template>

<xsl:template name="render-app-variation">
  <xsl:param name="style"/>
  <xsl:variable name="tooltip">
    <xsl:call-template name="app-tooltip-text"/>
  </xsl:variable>
  <span>
    <xsl:if test="$style != ''">
      <xsl:attribute name="style">
        <xsl:value-of select="$style"/>
      </xsl:attribute>
    </xsl:if>
    <xsl:attribute name="class">
      <xsl:call-template name="app-variation-classes"/>
    </xsl:attribute>
    <xsl:attribute name="data-tooltip">
      <xsl:value-of select="$tooltip"/>
    </xsl:attribute>
    <xsl:attribute name="data-default-tooltip">
      <xsl:value-of select="$tooltip"/>
    </xsl:attribute>
    <xsl:if test="normalize-space(tei:lem) = ''">
      <xsl:attribute name="tabindex">0</xsl:attribute>
      <xsl:attribute name="aria-label">
        <xsl:text>Apparat critique: </xsl:text>
        <xsl:value-of select="normalize-space($tooltip)"/>
      </xsl:attribute>
    </xsl:if>
    <xsl:choose>
      <xsl:when test="tei:lem">
        <xsl:call-template name="render-app-reading">
          <xsl:with-param name="reading" select="tei:lem[1]"/>
          <xsl:with-param name="kind">lem</xsl:with-param>
          <xsl:with-param name="is-default" select="true()"/>
        </xsl:call-template>
      </xsl:when>
      <xsl:otherwise>
        <span class="app-reading app-reading-default app-reading-active" data-kind="fallback" data-wits="">
          <xsl:value-of select="normalize-space(.)"/>
        </span>
      </xsl:otherwise>
    </xsl:choose>
    <xsl:for-each select="tei:rdg">
      <xsl:call-template name="render-app-reading">
        <xsl:with-param name="reading" select="."/>
        <xsl:with-param name="kind">rdg</xsl:with-param>
      </xsl:call-template>
    </xsl:for-each>
  </span>
</xsl:template>


  <xsl:template match="/tei:TEI">
    <html lang="fr">
      <head>
        <meta charset="UTF-8"/>
        <title>
          <xsl:choose>
            <xsl:when test="normalize-space((tei:teiHeader/tei:fileDesc/tei:titleStmt/tei:title)[1]) != ''">
              <xsl:value-of select="normalize-space((tei:teiHeader/tei:fileDesc/tei:titleStmt/tei:title)[1])"/>
            </xsl:when>
            <xsl:otherwise>Édition TEI</xsl:otherwise>
          </xsl:choose>
        </title>
        <link href="https://fonts.googleapis.com/css2?family=IM+Fell+DW+Pica&amp;display=swap" rel="stylesheet"/>
        <link href="https://fonts.googleapis.com/css2?family=EB+Garamond&amp;display=swap" rel="stylesheet"/>
        <link href="https://fonts.googleapis.com/css2?family=Source+Sans+Pro&amp;display=swap" rel="stylesheet"/>
        <style>
          html {
            scroll-behavior: smooth;
          }
          body {
            font-family: 'IM Fell DW Pica', Georgia, serif;
            background: #fdf6e3;
            color: #4a3c1a;
            padding: 2em;
            max-width: 800px;
            margin-left: 9em;
          }
          .ligne-logos-gauche {
           display: flex;
           align-items: center;
           gap: 1em;
           margin-bottom: 0.5em;
          }
          .logo-credit {
           width: 200px;
           height: auto;
           opacity: 0.85;
          }
          .logo-ekdosis {
           width: 50px;
           height: auto;
           opacity: 0.9;
          }
          .bloc-credit {
           font-family: 'Source Sans Pro', sans-serif;
           font-size: 0.8em;
           color: #3a3a3a;
           margin: 1.5em 0;
           padding: 0.6em 1.1em;
           border: 1px solid #ccc2b2;
           background: #fefdf8;
           line-height: 1.2;
           text-align: left;
           max-width: 650px;
           margin-left: auto;
           margin-right: auto;
           border-radius: 6px;
           box-shadow: 1px 1px 3px rgba(0, 0, 0, 0.04);
          }
          .italic {
            font-style: italic;
            color: darkred;
          }
          .bold {
            font-weight: bold;
          }
          .smallcaps {
            font-variant: small-caps;
          }
          .superscript {
            vertical-align: super;
            font-size: 0.8em;
            line-height: 0;
          }
          .subscript {
            vertical-align: sub;
            font-size: 0.8em;
            line-height: 0;
          }
          .underline {
            text-decoration: underline;
          }
          .acte-titre,
          .acte-titre-sans-variation,
          .scene-titre,
          .scene-titre-sans-variation,
          .personnages {
            font-weight: bold;
            margin-top: 1.5em;
            margin-bottom: 0.5em;
            margin-left: 11em;
          }
          .scene-titre {
            font-style: italic;
          }
          .locuteur {
            font-variant: small-caps;
            margin-top: 1em;
            margin-bottom: 0.2em;
            margin-left: 11em;
          }
          .tirade {
            margin-left: 1em;
            margin-bottom: 1em;
          }
          .didascalie {
            font-style: italic;
            color: #555;
            margin-left: 9em;
            margin-bottom: 0.5em;
          }
          .didas-implicites-label {
           text-align: right;
           font-style: normal;
           color: #777;
           font-weight: bold;
           font-size: 0.9em;
           margin: 0.5em 0 0.2em;
          }
          .stage-implicite {
           position: relative;
           padding-right: 6em;
           margin: 0.5em 0;
          }
          .stage-implicite::after {
           content: attr(data-label);
           position: absolute;
           top: 0;
           right: 0;
           font-style: italic;
           color: #777;
           font-size: 0.85em;
           white-space: nowrap;
          }
          .variation {
            position: relative;
            border-bottom: 1px dotted #8b5e3c;
            cursor: help;
          }
          .variation-empty {
            display: inline-block;
            min-width: 0.75em;
            min-height: 1em;
            line-height: 1;
            vertical-align: baseline;
            text-align: center;
          }
          .app-reading[hidden] {
            display: none !important;
          }
          .apparatus-controls {
            position: fixed;
            top: calc(var(--site-header-offset, 0px) + 0.75rem);
            right: 1rem;
            z-index: 1700;
            width: min(18rem, calc(100vw - 2rem));
            max-height: calc(100vh - var(--site-header-offset, 0px) - 1.5rem);
            overflow: auto;
            padding: 0.65rem 0.75rem;
            border: 1px solid #d2b47c;
            border-radius: 6px;
            background: rgba(254, 253, 248, 0.96);
            box-shadow: 0 6px 18px rgba(74, 60, 26, 0.14);
            font-family: 'Source Sans Pro', sans-serif;
            font-size: 0.88em;
            color: #4a3c1a;
          }
          .apparatus-controls h2 {
            margin: 0 0 0.35rem;
            font-size: 0.95rem;
          }
          .apparatus-controls label {
            display: block;
            margin-top: 0.25rem;
            cursor: pointer;
          }
          .apparatus-controls select {
            display: block;
            width: 100%;
            margin-top: 0.2rem;
          }
          .variation::after {
            content: attr(data-tooltip);
            position: absolute;
            top: 1.5em;
            left: 0;
            background: #fef3c7;
            color: #111;
            padding: 0.5em;
            border: 1px solid #e0b973;
            border-radius: 6px;
            font-size: 0.8em;
            white-space: pre-line;
            display: none;
            z-index: 1000;
            max-width: 400px;
            overflow-wrap: break-word;
          }
          .variation:hover::after,
          .variation:focus::after {
            display: block;
          }
          .hide-minor-variants .variation-minor,
          .hide-punctuation-variants .variation-punctuation-only,
          .hide-case-variants .variation-case-only,
          .hide-spacing-variants .variation-spacing-or-hyphen-only {
            border-bottom-color: transparent;
            cursor: inherit;
          }
          .hide-minor-variants .variation-minor::after,
          .hide-punctuation-variants .variation-punctuation-only::after,
          .hide-case-variants .variation-case-only::after,
          .hide-spacing-variants .variation-spacing-or-hyphen-only::after {
            content: none;
            display: none !important;
          }
          .hide-minor-variants .variation-minor.variation-empty,
          .hide-punctuation-variants .variation-punctuation-only.variation-empty,
          .hide-case-variants .variation-case-only.variation-empty,
          .hide-spacing-variants .variation-spacing-or-hyphen-only.variation-empty {
            display: inline;
            min-width: 0;
            width: 0;
            min-height: 0;
          }
          .vers-container {
            position: relative;
            margin-left: 5em;
            margin-bottom: 0.4em;
            line-height: 1;
          }
          .num-vers {
            position: absolute;
            left: -4.5em;
            width: 4em;
            text-align: right;
            font-size: 0.85em;
            color: #5a5245;
            font-style: italic;
          }
          .texte-vers {
            display: inline;
          }
          .vers-decale {
            margin-left: 14em;
          }
          .lg.stanza {
            margin-top: 0.8em;
            margin-bottom: 0.8em;
          }
          .vers-container.met-12 .texte-vers {
            display: inline-block;
            margin-left: 0;
          }
          .vers-container.met-11 .texte-vers {
            display: inline-block;
            margin-left: 1em;
          }
          .vers-container.met-10 .texte-vers {
            display: inline-block;
            margin-left: 2em;
          }
          .vers-container.met-9 .texte-vers {
            display: inline-block;
            margin-left: 3em;
          }
          .vers-container.met-8 .texte-vers {
            display: inline-block;
            margin-left: 4em;
          }
          .vers-container.met-7 .texte-vers {
            display: inline-block;
            margin-left: 5em;
          }
          .vers-container.met-6 .texte-vers {
            display: inline-block;
            margin-left: 6em;
          }
          .vers-container.met-5 .texte-vers {
            display: inline-block;
            margin-left: 7em;
          }
          .vers-container.met-4 .texte-vers {
            display: inline-block;
            margin-left: 8em;
          }
          .vers-container.met-3 .texte-vers {
            display: inline-block;
            margin-left: 9em;
          }
          .vers-container.met-2 .texte-vers {
            display: inline-block;
            margin-left: 10em;
          }
          .note-call {
            margin-left: 0.25em;
            font-size: 0.86em;
            line-height: 1;
          }
          .note-call a {
            text-decoration: none;
            color: #5b3f1f;
            font-weight: 600;
          }
          .note-call a:hover,
          .note-call a:focus {
            text-decoration: none;
            border-bottom: 1px solid #5b3f1f;
          }
          .note-call a:focus-visible {
            outline: 1px solid #7a5a2d;
            outline-offset: 1px;
          }
          .notes {
            margin: 1.5em 0 0 9em;
            padding-top: 0.5em;
            border-top: 1px solid #ccbba6;
          }
          .dramatis-personae {
            margin: 2em 0 2em 9em;
            max-width: 520px;
          }
          .dramatis-head {
            font-weight: bold;
            margin-left: 2em;
            margin-bottom: 0.8em;
          }
          .cast-list {
            list-style: none;
            padding-left: 0;
            margin: 0 0 1em 0;
          }
          .cast-item {
            margin: 0.25em 0;
          }
          .cast-role {
            font-variant: small-caps;
          }
          .cast-desc {
            font-style: italic;
          }
          .dramatis-personae .setting {
            margin-left: 0;
            margin-top: 1em;
          }
          .notes-title {
            font-size: 1.05em;
            margin-bottom: 0.6em;
          }
          .note-item {
            margin-bottom: 0.7em;
            padding: 0.25em 0.4em;
            border-radius: 4px;
          }
          .note-item p {
            margin: 0.35em 0;
          }
          .note-item:target {
            background: #fff5d9;
            box-shadow: 0 0 0 1px #e7d8be inset;
          }
          .note-backlink {
            margin-left: 0.45em;
            text-decoration: none;
          }
          .note-backlink:hover,
          .note-backlink:focus {
            text-decoration: underline;
          }
          @media (prefers-reduced-motion: reduce) {
            html {
              scroll-behavior: auto;
            }
          }
        </style>
        <link rel="icon" href="https://www.normandie.fr/sites/default/files/2021-03/favicon.ico" type="image/x-icon"/>
      </head>
      <body>
        <xsl:apply-templates select="tei:metadonnees"/>
        <div class="apparatus-controls" aria-label="Options d'affichage">
          <h2>Affichage</h2>
          <label>
            <span>Version affichée</span>
            <select data-witness-select="data-witness-select">
              <option value="">Lemme de référence</option>
              <xsl:for-each select="tei:teiHeader//tei:listWit/tei:witness[@xml:id]">
                <xsl:variable name="witness-id" select="@xml:id"/>
                <option value="{$witness-id}">
                  <xsl:value-of select="$witness-id"/>
                  <xsl:variable name="witness-label" select="normalize-space(.)"/>
                  <xsl:if test="$witness-label != ''">
                    <xsl:text> - </xsl:text>
                    <xsl:choose>
                      <xsl:when test="string-length($witness-label) &gt; 60">
                        <xsl:value-of select="substring($witness-label, 1, 57)"/>
                        <xsl:text>...</xsl:text>
                      </xsl:when>
                      <xsl:otherwise>
                        <xsl:value-of select="$witness-label"/>
                      </xsl:otherwise>
                    </xsl:choose>
                  </xsl:if>
                </option>
              </xsl:for-each>
            </select>
          </label>
          <fieldset>
            <legend>Variantes mineures</legend>
            <label>
              <input class="apparatus-toggle" data-hide-class="hide-minor-variants" type="checkbox" checked="checked"/>
              <span>Variantes mineures</span>
            </label>
            <label>
              <input id="toggle-punctuation-variants" class="apparatus-toggle" data-hide-class="hide-punctuation-variants" type="checkbox" checked="checked"/>
              <span>Variantes de ponctuation</span>
            </label>
            <label>
              <input class="apparatus-toggle" data-hide-class="hide-case-variants" type="checkbox" checked="checked"/>
              <span>Variantes de majuscules/minuscules</span>
            </label>
            <label>
              <input class="apparatus-toggle" data-hide-class="hide-spacing-variants" type="checkbox" checked="checked"/>
              <span>Variantes d'espacement / traits d'union</span>
            </label>
          </fieldset>
        </div>
        <xsl:if test=".//tei:stage[@type='DI']">
          <div class="didas-implicites-label">didas. implicites</div>
        </xsl:if>
        <xsl:apply-templates select="tei:text"/>
        <script>
          (function () {
            var toggles = Array.prototype.slice.call(document.querySelectorAll('.apparatus-toggle[data-hide-class]'));
            var witnessSelect = document.querySelector('[data-witness-select]');
            var storageKey = 'ets-witness-display';
            function isHiddenEmptyVariation(node) {
              var root = document.documentElement;
              return (
                (root.classList.contains('hide-minor-variants') &amp;&amp; node.classList.contains('variation-minor')) ||
                (root.classList.contains('hide-punctuation-variants') &amp;&amp; node.classList.contains('variation-punctuation-only')) ||
                (root.classList.contains('hide-case-variants') &amp;&amp; node.classList.contains('variation-case-only')) ||
                (root.classList.contains('hide-spacing-variants') &amp;&amp; node.classList.contains('variation-spacing-or-hyphen-only'))
              );
            }
            function hasWitness(reading, witness) {
              return (reading.getAttribute('data-wits') || '').split(/\s+/).filter(Boolean).indexOf(witness) !== -1;
            }
            function defaultReading(readings) {
              for (var i = 0; i &lt; readings.length; i += 1) {
                if (readings[i].classList.contains('app-reading-default')) {
                  return readings[i];
                }
              }
              return readings[0] || null;
            }
            function activeReadingFor(readings, witness) {
              if (witness) {
                for (var i = 0; i &lt; readings.length; i += 1) {
                  if (hasWitness(readings[i], witness)) {
                    return readings[i];
                  }
                }
              }
              return defaultReading(readings);
            }
            function updateVariationReading(node, witness) {
              var readings = Array.prototype.slice.call(node.children).filter(function (child) {
                return child.classList.contains('app-reading');
              });
              if (!readings.length) {
                return;
              }
              var active = activeReadingFor(readings, witness);
              readings.forEach(function (reading) {
                var isActive = reading === active;
                reading.hidden = !isActive;
                reading.classList.toggle('app-reading-active', isActive);
              });
              var isEmpty = !active || active.dataset.omission === 'true' || active.textContent.trim() === '';
              node.classList.toggle('variation-empty', isEmpty);
              if (isEmpty) {
                node.setAttribute('aria-label', 'Apparat critique: ' + (node.dataset.tooltip || node.dataset.defaultTooltip || ''));
              } else {
                node.removeAttribute('aria-label');
              }
            }
            function updateVariationTabStops() {
              document.querySelectorAll('.variation').forEach(function (node) {
                if (!node.classList.contains('variation-empty')) {
                  node.removeAttribute('tabindex');
                  return;
                }
                if (isHiddenEmptyVariation(node)) {
                  node.setAttribute('tabindex', '-1');
                } else {
                  node.setAttribute('tabindex', '0');
                }
              });
            }
            function updateApparatusVisibility() {
              toggles.forEach(function (toggle) {
                document.documentElement.classList.toggle(toggle.dataset.hideClass, !toggle.checked);
              });
              updateVariationTabStops();
            }
            function applyWitnessChoice() {
              var witness = witnessSelect ? witnessSelect.value : '';
              document.querySelectorAll('.variation').forEach(function (node) {
                updateVariationReading(node, witness);
              });
              updateVariationTabStops();
            }
            function selectHasOption(select, value) {
              return Array.prototype.slice.call(select.options).some(function (option) {
                return option.value === value;
              });
            }
            toggles.forEach(function (toggle) {
              toggle.addEventListener('change', updateApparatusVisibility);
            });
            if (witnessSelect) {
              try {
                var saved = window.localStorage.getItem(storageKey);
                if (saved &amp;&amp; selectHasOption(witnessSelect, saved)) {
                  witnessSelect.value = saved;
                }
              } catch (error) {
                // Local storage can be unavailable in some embedded previews.
              }
              witnessSelect.addEventListener('change', function () {
                try {
                  window.localStorage.setItem(storageKey, witnessSelect.value);
                } catch (error) {
                  // Keep the selector usable even when persistence is blocked.
                }
                applyWitnessChoice();
              });
            }
            applyWitnessChoice();
            updateApparatusVisibility();
          }());
        </script>
      </body>
    </html>
  </xsl:template>

  <xsl:template match="tei:seg">
    <xsl:apply-templates/>
  </xsl:template>

  <xsl:template match="tei:div[@type='act']/tei:head[not(tei:app)]">
    <div class="acte-titre-sans-variation">
      <xsl:apply-templates/>
    </div>
  </xsl:template>

<xsl:template match="tei:div[@type='act']/tei:head[tei:app]">
    <div class="acte-titre">
     <xsl:apply-templates/>
    </div>
</xsl:template>

  <xsl:template match="tei:div[@type='scene']/tei:head[not(tei:app)]">
    <div class="scene-titre-sans-variation">
      <xsl:apply-templates/>
    </div>
  </xsl:template>

  <xsl:template match="tei:div[@type='scene']/tei:head[tei:app]">
    <div class="scene-titre">
      <xsl:apply-templates/>
    </div>
  </xsl:template>

  <xsl:template match="tei:div[@type='scene']">
    <xsl:apply-templates select="node()[not(self::tei:note)]"/>
    <xsl:if test="tei:note[@target]">
      <section class="notes">
        <h2 class="notes-title">Notes</h2>
        <ol>
          <xsl:apply-templates select="tei:note[@target]" mode="note-item"/>
        </ol>
      </section>
    </xsl:if>
  </xsl:template>

  <xsl:template match="tei:stage[@type='DI']">
    <xsl:variable name="func" select="substring-after(@ana, '#')"/>
    <xsl:variable name="label">
      <xsl:choose>
        <xsl:when test="$func='SPC'">parole</xsl:when>
        <xsl:when test="$func='ASP'">aspect</xsl:when>
        <xsl:when test="$func='TMP'">temps</xsl:when>
        <xsl:when test="$func='EVT'">événement</xsl:when>
        <xsl:when test="$func='SET'">décor</xsl:when>
        <xsl:when test="$func='PROX'">proxémie</xsl:when>
        <xsl:when test="$func='ATT'">attitude</xsl:when>
        <xsl:when test="$func='VOI'">voix</xsl:when>
        <xsl:otherwise>
          <xsl:value-of select="$func"/>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <div class="stage-implicite" data-type="{$func}" data-label="{$label}">
      <xsl:apply-templates select="tei:l"/>
      <xsl:call-template name="render-note-calls"/>
    </div>
  </xsl:template>

  <xsl:template match="tei:stage[@type='characters' or @type='personnages']">
    <div class="personnages">
      <xsl:apply-templates/>
    </div>
  </xsl:template>

  <xsl:template match="tei:stage[@type='characters' or @type='personnages']/tei:app">
    <xsl:call-template name="render-app-variation">
      <xsl:with-param name="style">font-variant: small-caps;</xsl:with-param>
    </xsl:call-template>
  </xsl:template>

  <xsl:template match="tei:div[@type='dramatis-personae']">
    <section class="dramatis-personae">
      <xsl:apply-templates select="tei:head"/>
      <xsl:apply-templates select="tei:castList"/>
      <xsl:apply-templates select="tei:stage[@type='setting']"/>
    </section>
  </xsl:template>

  <xsl:template match="tei:div[@type='dramatis-personae']/tei:head">
    <div class="dramatis-head">
      <xsl:apply-templates/>
    </div>
  </xsl:template>

  <xsl:template match="tei:div[@type='dramatis-personae']/tei:castList">
    <ul class="cast-list">
      <xsl:apply-templates select="tei:castItem"/>
    </ul>
  </xsl:template>

  <xsl:template match="tei:div[@type='dramatis-personae']//tei:castItem">
    <li class="cast-item">
      <xsl:choose>
        <xsl:when test="tei:note[@type='semi-diplomatic']">
          <xsl:apply-templates select="tei:note[@type='semi-diplomatic']/node()"/>
        </xsl:when>
        <xsl:otherwise>
          <xsl:apply-templates select="tei:role"/>
          <xsl:if test="normalize-space(tei:roleDesc) != ''">
            <xsl:text>, </xsl:text>
            <xsl:apply-templates select="tei:roleDesc"/>
          </xsl:if>
        </xsl:otherwise>
      </xsl:choose>
    </li>
  </xsl:template>

  <xsl:template match="tei:div[@type='dramatis-personae']//tei:role">
    <span class="cast-role">
      <xsl:apply-templates/>
    </span>
  </xsl:template>

  <xsl:template match="tei:div[@type='dramatis-personae']//tei:roleDesc">
    <span class="cast-desc">
      <xsl:apply-templates/>
    </span>
  </xsl:template>

  <xsl:template match="tei:div[@type='dramatis-personae']/tei:stage[@type='setting']" priority="2">
    <p class="didascalie setting">
      <em><xsl:apply-templates/></em>
    </p>
  </xsl:template>

  <xsl:template match="tei:stage[not(@type='DI') and not(@type='characters') and not(@type='personnages')]">
    <p class="didascalie">
      <em><xsl:apply-templates/></em>
      <xsl:call-template name="render-note-calls"/>
    </p>
  </xsl:template>

  <xsl:template match="tei:sp">
    <div class="locuteur">
      <xsl:apply-templates select="tei:speaker"/>
    </div>
    <div class="tirade">
      <xsl:apply-templates select="tei:stage | tei:l | tei:lg"/>
    </div>
  </xsl:template>

  <xsl:template match="tei:lg[@type='stanza']">
    <div class="lg stanza">
      <xsl:if test="@subtype">
        <xsl:attribute name="data-subtype">
          <xsl:value-of select="@subtype"/>
        </xsl:attribute>
      </xsl:if>
      <xsl:if test="@rhyme">
        <xsl:attribute name="data-rhyme">
          <xsl:value-of select="@rhyme"/>
        </xsl:attribute>
      </xsl:if>
      <xsl:apply-templates select="tei:l"/>
    </div>
  </xsl:template>

  <xsl:template match="tei:speaker">
    <span style="font-variant: small-caps;">
      <xsl:apply-templates/>
    </span>
  </xsl:template>

  <xsl:template match="tei:speaker/tei:app">
    <xsl:call-template name="render-app-variation">
      <xsl:with-param name="style">font-variant: small-caps;</xsl:with-param>
    </xsl:call-template>
  </xsl:template>

  <xsl:template match="tei:l">
    <div>
      <xsl:attribute name="class">
        <xsl:text>vers-container l verse</xsl:text>
        <xsl:if test="@met">
          <xsl:text> met-</xsl:text>
          <xsl:value-of select="@met"/>
        </xsl:if>
        <xsl:if test="contains(@n, '.2')">
          <xsl:text> vers-decale</xsl:text>
        </xsl:if>
      </xsl:attribute>
      <xsl:choose>
        <xsl:when test="number(@n) mod 5 = 0">
          <span class="num-vers"><xsl:value-of select="@n"/></span>
        </xsl:when>
        <xsl:otherwise>
          <span class="num-vers"></span>
        </xsl:otherwise>
      </xsl:choose>
      <span class="texte-vers">
        <xsl:apply-templates/>
        <xsl:call-template name="render-note-calls"/>
      </span>
    </div>
  </xsl:template>

  <xsl:template match="tei:app">
    <xsl:call-template name="render-app-variation"/>
  </xsl:template>

  <xsl:template match="tei:hi">
    <span class="{@rend}">
      <xsl:apply-templates/>
    </span>
  </xsl:template>

  <xsl:template match="tei:ref">
    <a href="{@target}">
      <xsl:apply-templates/>
    </a>
  </xsl:template>

  <xsl:template match="tei:p">
    <p>
      <xsl:apply-templates/>
    </p>
  </xsl:template>

  <xsl:template match="tei:metadonnees">
    <div class="bloc-credit">
      <div class="ligne-logos-gauche">
        <img src="logos.png" alt="Logos" class="logo-credit"/>
      </div>
      <xsl:apply-templates select="tei:credit"/>
    </div>
  </xsl:template>

  <xsl:template match="tei:credit">
    <div class="credit-line">
      <xsl:apply-templates/>
    </div>
  </xsl:template>

  <xsl:template name="render-note-calls">
    <xsl:variable name="target-id" select="@xml:id"/>
    <xsl:if test="$target-id != ''">
      <xsl:for-each select="ancestor::tei:TEI//tei:note[@target and contains(concat(' ', normalize-space(@target), ' '), concat(' #', $target-id, ' '))]">
        <xsl:variable name="note-number" select="count(preceding::tei:note[@target]) + 1"/>
        <xsl:variable name="note-preview-full" select="normalize-space(string(.))"/>
        <xsl:variable name="note-preview">
          <xsl:choose>
            <xsl:when test="string-length($note-preview-full) &gt; 200">
              <xsl:value-of select="concat(substring($note-preview-full, 1, 200), '…')"/>
            </xsl:when>
            <xsl:otherwise>
              <xsl:value-of select="$note-preview-full"/>
            </xsl:otherwise>
          </xsl:choose>
        </xsl:variable>
        <sup class="note-call" id="noteref-{$note-number}-{$target-id}">
          <a href="#note-{$note-number}" title="{$note-preview}" aria-label="Note {$note-number}: {$note-preview}">
            <xsl:value-of select="$note-number"/>
          </a>
        </sup>
      </xsl:for-each>
    </xsl:if>
  </xsl:template>

  <xsl:template match="tei:note" mode="note-item">
    <xsl:variable name="note-number" select="count(preceding::tei:note[@target]) + 1"/>
    <xsl:variable name="first-target" select="substring-before(concat(normalize-space(substring-after(normalize-space(@target), '#')), ' '), ' ')"/>
    <li id="note-{$note-number}" class="note-item">
      <xsl:choose>
        <xsl:when test="tei:p">
          <xsl:apply-templates/>
        </xsl:when>
        <xsl:otherwise>
          <p><xsl:apply-templates/></p>
        </xsl:otherwise>
      </xsl:choose>
      <xsl:if test="$first-target != ''">
        <a href="#noteref-{$note-number}-{$first-target}" class="note-backlink">&#8617;</a>
      </xsl:if>
    </li>
  </xsl:template>

  <xsl:template match="tei:note"/>

  <xsl:template match="tei:rdg"/>
</xsl:stylesheet>
