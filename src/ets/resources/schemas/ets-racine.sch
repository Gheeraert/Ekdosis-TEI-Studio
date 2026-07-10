<?xml version="1.0" encoding="UTF-8"?>
<schema xmlns="http://purl.oclc.org/dsdl/schematron"
        xmlns:tei="http://www.tei-c.org/ns/1.0"
        queryBinding="xslt">
  <ns prefix="tei" uri="http://www.tei-c.org/ns/1.0"/>
  <ns prefix="xml" uri="http://www.w3.org/XML/1998/namespace"/>

  <pattern id="ets-racine-dramatic-profile">
    <rule context="tei:text">
      <assert test="@xml:id">text must have @xml:id.</assert>
    </rule>

    <rule context="tei:body">
      <assert test="not(*[not(self::tei:div[@type='act'])])">body must contain only div type="act".</assert>
    </rule>

    <rule context="tei:div">
      <assert test="not(@type='act') or @n">div type="act" must have @n.</assert>
      <assert test="not(@type='act') or @xml:id">div type="act" must have @xml:id.</assert>
      <assert test="not(@type='act') or tei:head">div type="act" must have a head.</assert>
      <assert test="not(@type='act') or tei:div[@type='scene']">div type="act" must contain at least one scene.</assert>
      <assert test="not(@type='scene') or @n">div type="scene" must have @n.</assert>
      <assert test="not(@type='scene') or @xml:id">div type="scene" must have @xml:id.</assert>
      <assert test="not(@type='scene') or tei:head">div type="scene" must have a head.</assert>
      <assert test="not(@type='scene') or tei:sp">div type="scene" must contain at least one sp.</assert>
    </rule>

    <rule context="tei:l">
      <assert test="@n">l must have @n.</assert>
      <assert test="@xml:id">l must have @xml:id.</assert>
      <assert test="not(@part) or @part = 'I' or @part = 'M' or @part = 'F'">l/@part must be I, M or F.</assert>
      <assert test="not(contains(@n, '.')) or @part">decimal shared-verse l/@n values must have @part.</assert>
      <assert test="not(@part) or contains(@n, '.')">l/@part is only allowed on decimal shared-verse numbers.</assert>
    </rule>

    <rule context="tei:app">
      <assert test="count(tei:lem) = 1 and count(tei:rdg) &gt;= 1">app must contain exactly one lem and at least one rdg.</assert>
      <assert test="tei:lem[1][not(preceding-sibling::*)]">app must start with lem.</assert>
      <assert test="not(tei:rdg[preceding-sibling::*[not(self::tei:lem or self::tei:rdg)]])">app must contain lem followed by rdg elements.</assert>
      <assert test="not(@type='minor') or @subtype">app type="minor" must have @subtype.</assert>
      <assert test="not(@type='minor') or @ana">app type="minor" must have @ana.</assert>
      <assert test="not(@subtype) or @subtype = 'graphic' or @subtype = 'punctuation' or @subtype = 'mixed' or @subtype = 'case' or @subtype = 'spacing' or @subtype = 'identical'">app/@subtype must use an ETS minor-variant category.</assert>
    </rule>

    <rule context="tei:witness">
      <assert test="not(@ana) or @ana = '#witness_documentary' or @ana = '#witness_editorial'">witness/@ana must be #witness_documentary or #witness_editorial when present.</assert>
      <assert test="not(@ana = '#witness_documentary' or @ana = '#witness_editorial') or count(/tei:TEI/tei:teiHeader/tei:encodingDesc/tei:classDecl/tei:taxonomy[@xml:id='ets-witness-taxonomy']) = 1">witness/@ana requires exactly one ets-witness-taxonomy.</assert>
      <assert test="not(@ana = '#witness_documentary') or /tei:TEI/tei:teiHeader/tei:encodingDesc/tei:classDecl/tei:taxonomy[@xml:id='ets-witness-taxonomy']/tei:category[@xml:id='witness_documentary']">witness/@ana #witness_documentary must target a declared witness_documentary category.</assert>
      <assert test="not(@ana = '#witness_editorial') or /tei:TEI/tei:teiHeader/tei:encodingDesc/tei:classDecl/tei:taxonomy[@xml:id='ets-witness-taxonomy']/tei:category[@xml:id='witness_editorial']">witness/@ana #witness_editorial must target a declared witness_editorial category.</assert>
    </rule>

    <rule context="tei:teiHeader">
      <assert test="count(.//tei:taxonomy[@xml:id='ets-witness-taxonomy']) &lt;= 1">There must not be more than one ets-witness-taxonomy.</assert>
      <assert test="not(.//tei:taxonomy[@xml:id='ets-witness-taxonomy']) or .//tei:taxonomy[@xml:id='ets-witness-taxonomy']/tei:category[@xml:id='witness_documentary']">ets-witness-taxonomy must declare witness_documentary.</assert>
      <assert test="not(.//tei:taxonomy[@xml:id='ets-witness-taxonomy']) or .//tei:taxonomy[@xml:id='ets-witness-taxonomy']/tei:category[@xml:id='witness_editorial']">ets-witness-taxonomy must declare witness_editorial.</assert>
    </rule>

    <rule context="tei:lem">
      <assert test="@wit">lem and rdg must have @wit.</assert>
      <assert test="not(@wit) or starts-with(normalize-space(@wit), '#')">lem/rdg @wit values must point to declared witness/@xml:id values; multi-token resolution is checked in Python tests.</assert>
      <assert test="not(@type = 'omission') or normalize-space(.) = ''">lem type="omission" must be textually empty.</assert>
      <assert test="normalize-space(.) != '(lacune)'">Literal ETS lacuna marker must not be kept as a complete lem reading.</assert>
    </rule>

    <rule context="tei:rdg">
      <assert test="@wit">lem and rdg must have @wit.</assert>
      <assert test="not(@wit) or starts-with(normalize-space(@wit), '#')">lem/rdg @wit values must point to declared witness/@xml:id values; multi-token resolution is checked in Python tests.</assert>
      <assert test="not(@type = 'omission') or normalize-space(.) = ''">rdg type="omission" must be textually empty.</assert>
      <assert test="normalize-space(.) != '(lacune)'">Literal ETS lacuna marker must not be kept as a complete rdg reading.</assert>
    </rule>

    <rule context="tei:hi">
      <assert test="@rend = 'italic'">hi/@rend must be italic.</assert>
    </rule>

    <rule context="tei:stage">
      <assert test="not(@type='personnages') or not(@xml:id)">stage type="personnages" must not have @xml:id.</assert>
      <assert test="not(@type='DI') or @xml:id">stage type="DI" must have @xml:id.</assert>
      <assert test="not(@type='DI') or @ana">stage type="DI" must have @ana.</assert>
      <assert test="not(@type='DI') or tei:l">stage type="DI" must contain at least one l.</assert>
      <assert test="not(@type='DI') or @ana = '#SPC' or @ana = '#ASP' or @ana = '#TMP' or @ana = '#EVT' or @ana = '#SET' or @ana = '#PROX' or @ana = '#ATT' or @ana = '#VOI'">stage type="DI"/@ana must use an ETS implicit-stage category.</assert>
    </rule>

    <rule context="tei:lg">
      <assert test="@type = 'stanza'">lg must have @type="stanza".</assert>
      <assert test="tei:l">lg type="stanza" must contain at least one l.</assert>
    </rule>

    <rule context="*">
      <assert test="not(@xml:id) or count(//*[@xml:id = current()/@xml:id]) = 1">Structural xml:id values must be unique.</assert>
    </rule>

    <rule context="tei:l">
      <assert test="not(ancestor::tei:text/@xml:id) or starts-with(@xml:id, concat(ancestor::tei:text/@xml:id, '-'))">Structural xml:id values for acts, scenes, lines, explicit stages, and stage type="DI" should start with the play id followed by "-".</assert>
    </rule>

    <rule context="tei:div">
      <assert test="not(@type='act' or @type='scene') or not(ancestor::tei:text/@xml:id) or starts-with(@xml:id, concat(ancestor::tei:text/@xml:id, '-'))">Structural xml:id values for acts, scenes, lines, explicit stages, and stage type="DI" should start with the play id followed by "-".</assert>
    </rule>

    <rule context="tei:stage">
      <assert test="@type='personnages' or not(ancestor::tei:text/@xml:id) or starts-with(@xml:id, concat(ancestor::tei:text/@xml:id, '-'))">Structural xml:id values for acts, scenes, lines, explicit stages, and stage type="DI" should start with the play id followed by "-".</assert>
    </rule>
  </pattern>
</schema>
