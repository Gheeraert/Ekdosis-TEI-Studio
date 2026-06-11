(function () {
  'use strict';

  var container = document.getElementById('plays-container');
  var addBtn = document.getElementById('add-play-btn');

  function _suffix(name) {
    var m = name.match(/^play_\d+_(.+)$/);
    return m ? m[1] : name;
  }

  function _buildBlock(idx) {
    var div = document.createElement('div');
    div.className = 'play-block';
    div.dataset.playIndex = String(idx);

    var h4 = document.createElement('h4');
    h4.textContent = 'Pièce ' + (idx + 1);
    div.appendChild(h4);

    [
      { suffix: 'xml',      label: 'XML de la pièce (.xml uniquement)',          accept: '.xml' },
      { suffix: 'notice',   label: 'Notice (.docx ou .xml, optionnel)',           accept: '.docx,.xml' },
      { suffix: 'preface',  label: 'Préface (.docx ou .xml, optionnel)',          accept: '.docx,.xml' },
      { suffix: 'dramatis', label: 'Dramatis personae (.xml uniquement, optionnel)', accept: '.xml' },
    ].forEach(function (f) {
      var fieldDiv = document.createElement('div');
      fieldDiv.className = 'field';
      var lbl = document.createElement('label');
      lbl.textContent = f.label;
      var inp = document.createElement('input');
      inp.type = 'file';
      inp.name = 'play_' + idx + '_' + f.suffix;
      inp.accept = f.accept;
      inp.dataset.suffix = f.suffix;
      var hint = document.createElement('span');
      hint.className = 'filename-hint';
      hint.style.cssText = 'font-size:0.85em;color:#666;margin-left:0.5em;';
      fieldDiv.appendChild(lbl);
      fieldDiv.appendChild(inp);
      fieldDiv.appendChild(hint);
      div.appendChild(fieldDiv);
    });

    var removeDiv = document.createElement('div');
    removeDiv.className = 'field';
    var removeBtn = document.createElement('button');
    removeBtn.type = 'button';
    removeBtn.className = 'remove-play-btn';
    removeBtn.textContent = 'Retirer cette pièce';
    removeBtn.addEventListener('click', function () {
      container.removeChild(div);
      _renumber();
    });
    removeDiv.appendChild(removeBtn);
    div.appendChild(removeDiv);

    return div;
  }

  function _renumber() {
    var blocks = container.querySelectorAll('.play-block');
    blocks.forEach(function (block, i) {
      block.dataset.playIndex = String(i);
      var h4 = block.querySelector('h4');
      if (h4) { h4.textContent = 'Pièce ' + (i + 1); }
      block.querySelectorAll('input[type="file"]').forEach(function (inp) {
        var suf = inp.dataset.suffix || _suffix(inp.name);
        inp.name = 'play_' + i + '_' + suf;
        inp.dataset.suffix = suf;
      });
    });
  }

  if (addBtn) {
    addBtn.addEventListener('click', function () {
      var count = container.querySelectorAll('.play-block').length;
      container.appendChild(_buildBlock(count));
    });
  }

  // Config JSON import
  var loadBtn = document.getElementById('load-config-btn');
  if (loadBtn) {
    loadBtn.addEventListener('click', function () {
      var fileInput = document.getElementById('builder_config_file');
      var file = fileInput.files[0];
      if (!file) { alert('Sélectionnez d\'abord un fichier de configuration JSON.'); return; }
      var reader = new FileReader();
      reader.onload = function (e) {
        var data;
        try { data = JSON.parse(e.target.result); } catch (err) {
          alert('Fichier JSON invalide : ' + err.message); return;
        }
        if (data.schema !== 'ets.builder_form_config') {
          alert('Ce fichier n\'est pas une configuration du constructeur ETS.'); return;
        }

        function setField(name, value) {
          var el = document.querySelector('[name="' + name + '"]');
          if (el && value !== undefined && value !== null) { el.value = value; }
        }
        function setCheck(name, value) {
          var el = document.querySelector('[name="' + name + '"]');
          if (el) { el.checked = !!value; }
        }

        setField('author_first_name', data.author_first_name);
        setField('author_last_name', data.author_last_name);
        setField('corpus_title', data.corpus_title);
        setField('editor_first_name', data.editor_first_name);
        setField('editor_last_name', data.editor_last_name);
        if (data.options) {
          setCheck('publish_notices', data.options.publish_notices);
          setCheck('publish_prefaces', data.options.publish_prefaces);
          setCheck('include_metadata', data.options.include_metadata);
          setCheck('resolve_notice_xincludes', data.options.resolve_notice_xincludes);
        }

        // Restore play blocks
        if (Array.isArray(data.plays) && data.plays.length > 0) {
          var existing = Array.from(container.querySelectorAll('.play-block'));
          for (var i = 1; i < existing.length; i++) {
            container.removeChild(existing[i]);
          }
          var needed = data.plays.length;
          var current = container.querySelectorAll('.play-block').length;
          for (var j = current; j < needed; j++) {
            container.appendChild(_buildBlock(j));
          }
          data.plays.forEach(function (play, idx) {
            var block = container.querySelectorAll('.play-block')[idx];
            if (!block) { return; }
            var hintMap = {
              xml:      play.expected_xml_filename,
              notice:   play.expected_notice_filename,
              preface:  play.expected_preface_filename,
              dramatis: play.expected_dramatis_filename,
            };
            Object.keys(hintMap).forEach(function (suf) {
              var hint = hintMap[suf];
              if (!hint) { return; }
              var inp = block.querySelector('input[name="play_' + idx + '_' + suf + '"]');
              if (!inp) { return; }
              var span = inp.nextElementSibling;
              if (span && span.classList.contains('filename-hint')) {
                span.textContent = '(attendu : ' + hint + ')';
              }
            });
          });
        }
      };
      reader.readAsText(file);
    });
  }
})();
