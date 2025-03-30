<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="2.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:tei="http://www.tei-c.org/ns/1.0"
    exclude-result-prefixes="tei">

  <xsl:output method="html" encoding="UTF-8" indent="yes"/>

  <xsl:template match="/tei:TEI">
    <html lang="fr">
      <head>
        <meta charset="UTF-8"/>
        <title>Édition TEI</title>
        <xsl:text disable-output-escaping="yes">
          <![CDATA[<link href="https://fonts.googleapis.com/css2?family=IM+Fell+DW+Pica&display=swap" rel="stylesheet">]]>
        </xsl:text>
        <style>
          body {
            font-family: 'IM Fell DW Pica', Georgia, serif;
            background: #fdf6e3;
            color: #4a3c1a;
            padding: 2em;
            max-width: 800px;
            margin-left: 9em;
          }
          .acte, .scene, .personnages {
            font-weight: bold;
            margin-top: 1.5em;
            margin-bottom: 0.5em;
            margin-left: 9em;
          }
          .scene-titre {
            font-style: italic;
            margin-bottom: 0.5em;
            margin-left: 9em;
          }
          .locuteur {
            font-variant: small-caps;
            margin-top: 1em;
            margin-bottom: 0.2em;
            margin-left: 9em;
          }
          .tirade {
            margin-left: 1em;
            margin-bottom: 1em;
          }
          .vers {
            margin: 0.2em 0;
          }
          .didascalie {
            font-style: italic;
            color: #555;
            margin-left: 7em;
            margin-bottom: 0.5em;
          }
          .variation {
            border-bottom: 1px dotted #8b5e3c;
            cursor: help;
          }
        </style>
      </head>
      <body>
        <xsl:apply-templates/>
      </body>
    </html>
  </xsl:template>

  <!-- Acte -->
  <xsl:template match="tei:div[@type='act']">
    <div class="acte">ACTE <xsl:value-of select="@n"/></div>
    <xsl:apply-templates/>
  </xsl:template>

  <!-- Titre de scène -->
  <xsl:template match="tei:head">
    <div class="scene-titre"><xsl:apply-templates/></div>
  </xsl:template>

  <!-- Didascalies -->
  <xsl:template match="tei:stage">
    <div class="didascalie"><xsl:apply-templates/></div>
  </xsl:template>

  <!-- Bloc de parole -->
  <xsl:template match="tei:sp">
    <div class="locuteur"><xsl:value-of select="tei:speaker"/></div>
    <div class="tirade">
      <xsl:apply-templates select="tei:l"/>
    </div>
  </xsl:template>

  <!-- Vers -->
  <xsl:template match="tei:l">
    <div class="vers"><xsl:apply-templates/></div>
  </xsl:template>

  <!-- Variantes : infobulle au survol -->
  <xsl:template match="tei:app">
    <xsl:variable name="tooltip">
      <xsl:for-each select="tei:rdg">
        <xsl:value-of select="@wit"/>
        <xsl:text>: </xsl:text>
        <xsl:value-of select="normalize-space(.)"/>
        <xsl:if test="position() != last()">
          <xsl:text>&#10;</xsl:text>
        </xsl:if>
      </xsl:for-each>
    </xsl:variable>

    <span class="variation">
      <xsl:attribute name="title">
        <xsl:value-of select="$tooltip"/>
      </xsl:attribute>
      <xsl:apply-templates select="tei:lem"/>
    </span>
  </xsl:template>

  <!-- On ignore les rdg dans le texte courant -->
  <xsl:template match="tei:rdg"/>
</xsl:stylesheet>
