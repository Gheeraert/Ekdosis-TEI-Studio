<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:tei="http://www.tei-c.org/ns/1.0"
  exclude-result-prefixes="tei">

  <xsl:output method="html" encoding="UTF-8" indent="yes"/>

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
          .variation:hover::after {
            display: block;
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
        </style>
        <link rel="icon" href="https://www.normandie.fr/sites/default/files/2021-03/favicon.ico" type="image/x-icon"/>
      </head>
      <body>
        <xsl:apply-templates select="tei:metadonnees"/>
        <xsl:if test=".//tei:stage[@type='DI']">
          <div class="didas-implicites-label">didas. implicites</div>
        </xsl:if>
        <xsl:apply-templates select="tei:text"/>
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
      <xsl:apply-templates select="tei:app"/>
    </div>
  </xsl:template>

  <xsl:template match="tei:div[@type='scene']/tei:head[not(tei:app)]">
    <div class="scene-titre-sans-variation">
      <xsl:apply-templates/>
    </div>
  </xsl:template>

  <xsl:template match="tei:div[@type='scene']/tei:head[tei:app]">
    <div class="scene-titre">
      <xsl:apply-templates select="tei:app"/>
    </div>
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
    </div>
  </xsl:template>

  <xsl:template match="tei:stage[@type='characters' or @type='personnages']">
    <div class="personnages">
      <xsl:apply-templates/>
    </div>
  </xsl:template>

  <xsl:template match="tei:stage[@type='characters' or @type='personnages']/tei:app">
    <span class="variation" style="font-variant: small-caps;">
      <xsl:attribute name="data-tooltip">
        <xsl:for-each select="tei:rdg">
          <xsl:value-of select="@wit"/>
          <xsl:text>: </xsl:text>
          <xsl:value-of select="normalize-space(.)"/>
          <xsl:text>&#10;&#10;</xsl:text>
        </xsl:for-each>
      </xsl:attribute>
      <xsl:apply-templates select="tei:lem"/>
    </span>
  </xsl:template>

  <xsl:template match="tei:stage[not(@type='DI') and not(@type='characters') and not(@type='personnages')]">
    <p class="didascalie"><em><xsl:apply-templates/></em></p>
  </xsl:template>

  <xsl:template match="tei:sp">
    <div class="locuteur">
      <xsl:apply-templates select="tei:speaker"/>
    </div>
    <div class="tirade">
      <xsl:apply-templates select="tei:stage | tei:l"/>
    </div>
  </xsl:template>

  <xsl:template match="tei:speaker">
    <span style="font-variant: small-caps;">
      <xsl:apply-templates/>
    </span>
  </xsl:template>

  <xsl:template match="tei:speaker/tei:app">
    <span class="variation" style="font-variant: small-caps;">
      <xsl:attribute name="data-tooltip">
        <xsl:for-each select="tei:rdg">
          <xsl:value-of select="@wit"/>
          <xsl:text>: </xsl:text>
          <xsl:value-of select="normalize-space(.)"/>
          <xsl:text>&#10;&#10;</xsl:text>
        </xsl:for-each>
      </xsl:attribute>
      <xsl:apply-templates select="tei:lem"/>
    </span>
  </xsl:template>

  <xsl:template match="tei:l">
    <div>
      <xsl:attribute name="class">
        <xsl:text>vers-container</xsl:text>
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
      </span>
    </div>
  </xsl:template>

  <xsl:template match="tei:app">
    <span class="variation">
      <xsl:attribute name="data-tooltip">
        <xsl:for-each select="tei:rdg">
          <xsl:value-of select="@wit"/>
          <xsl:text>: </xsl:text>
          <xsl:value-of select="normalize-space(.)"/>
          <xsl:text>&#10;&#10;</xsl:text>
        </xsl:for-each>
      </xsl:attribute>
      <xsl:apply-templates select="tei:lem"/>
    </span>
  </xsl:template>

  <xsl:template match="tei:hi">
    <span class="{@rend}">
      <xsl:apply-templates/>
    </span>
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

  <xsl:template match="tei:rdg"/>
</xsl:stylesheet>
