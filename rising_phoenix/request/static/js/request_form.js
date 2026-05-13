(function () {
  'use strict';

  var shell = document.querySelector('.request-shell');
  var refineUrl = shell ? shell.dataset.refineUrl : '';
  var suggestedArtisansUrl = shell ? shell.dataset.suggestedArtisansUrl : '';

  function getCsrfToken() {
    var input = document.querySelector('input[name="csrfmiddlewaretoken"]');
    return input ? input.value : '';
  }

  // AI refine block
  (function () {
    var refineBtn = document.getElementById('ai-refine-btn');
    var statusEl = document.getElementById('ai-refine-status');
    var descriptionEl = document.getElementById('id_description');
    var panelEl = document.getElementById('ai-review-panel');
    var originalEl = document.getElementById('ai-original-text');
    var suggestedEl = document.getElementById('ai-suggested-text');
    var diffOutputEl = document.getElementById('ai-diff-output');
    var acceptBtn = document.getElementById('ai-accept-btn');
    var retryBtn = document.getElementById('ai-retry-btn');
    var rejectBtn = document.getElementById('ai-reject-btn');
    var loaderEl = document.getElementById('ai-refine-loader');

    if (!refineBtn || !statusEl || !descriptionEl || !panelEl || !originalEl || !suggestedEl || !diffOutputEl || !acceptBtn || !retryBtn || !rejectBtn || !loaderEl || !refineUrl) {
      return;
    }

    function escapeHtml(value) {
      return value
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/\"/g, '&quot;')
        .replace(/'/g, '&#039;');
    }

    function renderDiff(sourceText, suggestedText) {
      var sourceWords = sourceText.split(/\s+/).filter(Boolean);
      var suggestedWords = suggestedText.split(/\s+/).filter(Boolean);
      var sourceSet = new Set(sourceWords);
      var suggestedSet = new Set(suggestedWords);

      var removed = sourceWords
        .filter(function (word) { return !suggestedSet.has(word); })
        .map(function (word) { return '<span class="diff-removed">-' + escapeHtml(word) + '</span>'; })
        .join(' ');

      var added = suggestedWords
        .filter(function (word) { return !sourceSet.has(word); })
        .map(function (word) { return '<span class="diff-added">+' + escapeHtml(word) + '</span>'; })
        .join(' ');

      var sections = [];
      if (added) {
        sections.push('<p class="mb-2"><strong>Added:</strong> ' + added + '</p>');
      }
      if (removed) {
        sections.push('<p class="mb-0"><strong>Removed:</strong> ' + removed + '</p>');
      }
      if (!sections.length) {
        sections.push('<p class="mb-0">No visible word changes found yet.</p>');
      }

      diffOutputEl.innerHTML = sections.join('');
    }

    function setBusy(isBusy) {
      refineBtn.disabled = isBusy;
      retryBtn.disabled = isBusy;
      acceptBtn.disabled = isBusy;
      rejectBtn.disabled = isBusy;
      loaderEl.hidden = !isBusy;
      refineBtn.textContent = isBusy ? 'Processing...' : 'Refine with AI';
    }

    async function refineText(text) {
      if (!text) {
        statusEl.textContent = 'Write a short description first.';
        statusEl.classList.add('error');
        return;
      }

      setBusy(true);
      statusEl.textContent = 'Thinking...';
      statusEl.classList.remove('error');

      try {
        var response = await fetch(refineUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
          },
          body: JSON.stringify({ text: text })
        });

        var data = await response.json();
        if (!response.ok) {
          throw new Error(data.error || 'Refinement failed.');
        }

        originalEl.value = descriptionEl.value;
        suggestedEl.value = data.refined_text;
        panelEl.hidden = false;
        renderDiff(originalEl.value, suggestedEl.value);
        statusEl.textContent = 'Review AI changes below, then accept, reject, or send back.';
      } catch (error) {
        statusEl.textContent = error.message || 'Something went wrong.';
        statusEl.classList.add('error');
      } finally {
        setBusy(false);
      }
    }

    refineBtn.addEventListener('click', async function () {
      await refineText(descriptionEl.value.trim());
    });

    suggestedEl.addEventListener('input', function () {
      renderDiff(originalEl.value, suggestedEl.value);
    });

    acceptBtn.addEventListener('click', function () {
      descriptionEl.value = suggestedEl.value.trim();
      panelEl.hidden = true;
      statusEl.textContent = 'AI suggestion accepted. You can still edit before posting.';
      statusEl.classList.remove('error');
    });

    rejectBtn.addEventListener('click', function () {
      panelEl.hidden = true;
      statusEl.textContent = 'AI suggestion rejected. Your original description is unchanged.';
      statusEl.classList.remove('error');
    });

    retryBtn.addEventListener('click', async function () {
      await refineText(suggestedEl.value.trim());
    });
  })();

  // Multi-image preview block
  (function () {
    var input = document.getElementById('id_reference_images');
    var zone = document.getElementById('img-upload-zone');
    var prompt = document.getElementById('img-upload-prompt');
    var grid = document.getElementById('img-preview-grid');
    if (!input || !zone || !grid) {
      return;
    }

    var accumulated = new DataTransfer();

    function syncInput() {
      input.files = accumulated.files;
    }

    function fileKey(file) {
      return [file.name, file.size, file.lastModified].join('::');
    }

    function removeFile(targetKey) {
      var fresh = new DataTransfer();
      Array.from(accumulated.files).forEach(function (file) {
        if (fileKey(file) !== targetKey) {
          fresh.items.add(file);
        }
      });

      while (accumulated.items.length) {
        accumulated.items.remove(0);
      }

      Array.from(fresh.files).forEach(function (file) {
        accumulated.items.add(file);
      });

      syncInput();
      renderPreviews();
    }

    function renderPreviews() {
      grid.innerHTML = '';
      var files = Array.from(accumulated.files);

      if (!files.length) {
        grid.hidden = true;
        prompt.hidden = false;
        return;
      }

      prompt.hidden = true;
      grid.hidden = false;

      files.forEach(function (file) {
        var key = fileKey(file);
        var reader = new FileReader();

        reader.onload = function (event) {
          var wrap = document.createElement('div');
          wrap.className = 'img-preview-item';

          var img = document.createElement('img');
          img.src = event.target.result;
          img.alt = file.name;

          var trash = document.createElement('button');
          trash.type = 'button';
          trash.className = 'img-preview-remove';
          trash.title = 'Remove ' + file.name;
          trash.innerHTML = '&#128465;';
          trash.addEventListener('click', function () {
            removeFile(key);
          });

          var name = document.createElement('p');
          name.className = 'img-preview-name';
          name.textContent = file.name;

          wrap.appendChild(img);
          wrap.appendChild(trash);
          wrap.appendChild(name);
          grid.appendChild(wrap);
        };

        reader.readAsDataURL(file);
      });
    }

    function addFiles(newFiles) {
      var existing = new Set(
        Array.from(accumulated.files).map(function (file) {
          return fileKey(file);
        })
      );

      Array.from(newFiles).forEach(function (file) {
        var key = fileKey(file);
        if (file.type.startsWith('image/') && !existing.has(key)) {
          accumulated.items.add(file);
          existing.add(key);
        }
      });

      syncInput();
      renderPreviews();
    }

    input.addEventListener('change', function () {
      addFiles(this.files);
    });

    zone.addEventListener('dragover', function (event) {
      event.preventDefault();
      zone.classList.add('drag-over');
    });

    zone.addEventListener('dragleave', function () {
      zone.classList.remove('drag-over');
    });

    zone.addEventListener('drop', function (event) {
      event.preventDefault();
      zone.classList.remove('drag-over');
      addFiles(event.dataTransfer.files);
    });
  })();

  // Suggested artisans block
  (function () {
    var categoryInput = document.getElementById('id_category');
    var panel = document.getElementById('suggested-artisans-panel');
    var list = document.getElementById('suggested-artisans-list');

    if (!categoryInput || !panel || !list || !suggestedArtisansUrl) {
      return;
    }

    function renderCards(items) {
      if (!items.length) {
        list.innerHTML = '<p class="suggested-empty">No matching artisans found yet for this category.</p>';
        panel.hidden = false;
        return;
      }

      list.innerHTML = items
        .map(function (item) {
          var tagline = item.tagline ? item.tagline : 'Custom craft specialist';
          var location = item.location ? item.location : 'Location not specified';
          return (
            '<a class="suggested-card" href="' + item.workshop_url + '">' +
              '<p class="suggested-name">' + item.workshop_name + '</p>' +
              '<p class="suggested-by">by @' + item.artisan_username + '</p>' +
              '<p class="suggested-tagline">' + tagline + '</p>' +
              '<p class="suggested-location">' + location + '</p>' +
            '</a>'
          );
        })
        .join('');

      panel.hidden = false;
    }

    async function loadSuggestions() {
      var categoryId = categoryInput.value;
      if (!categoryId) {
        panel.hidden = true;
        return;
      }

      try {
        var response = await fetch(
          suggestedArtisansUrl + '?category_id=' + encodeURIComponent(categoryId)
        );
        var data = await response.json();
        renderCards(data.artisans || []);
      } catch (error) {
        list.innerHTML = '<p class="suggested-empty">Could not load suggestions right now.</p>';
        panel.hidden = false;
      }
    }

    categoryInput.addEventListener('change', loadSuggestions);
    loadSuggestions();
  })();
})();
