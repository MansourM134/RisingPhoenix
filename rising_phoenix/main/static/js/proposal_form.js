(function () {
  'use strict';

  // ── Image upload + draw/highlight editor ──────────────────────────────────
  (function () {
    var input = document.getElementById('id_proposal_images');
    var zone = document.getElementById('img-upload-zone');
    var grid = document.getElementById('img-preview-grid');
    var form = document.querySelector('.request-form-card form');

    var editorModal = document.getElementById('image-editor-modal');
    var editorCloseBtn = document.getElementById('image-editor-close');
    var editorHost = document.getElementById('image-editor-host');
    var saveBtn = document.getElementById('editor-save');
    var cancelBtn = document.getElementById('editor-cancel');
    var undoBtn = document.getElementById('editor-undo');
    var clearAllBtn = document.getElementById('editor-clear-all');
    var modeDrawBtn = document.getElementById('editor-mode-draw');
    var modeHighlightBtn = document.getElementById('editor-mode-highlight');
    var widthThinBtn = document.getElementById('editor-width-thin');
    var widthThickBtn = document.getElementById('editor-width-thick');
    var colorGroup = document.getElementById('editor-color-group');
    var widthGroup = document.getElementById('editor-width-group');

    if (!input || !zone || !grid || !form || !editorModal || !editorCloseBtn || !editorHost || !saveBtn || !cancelBtn) {
      return;
    }

    var MAX_IMAGES = 5;
    var items = [];
    var nextId = 1;
    var editorCurrentItemId = null;
    var editorImageType = 'image/jpeg';

    var editorCanvas = null;
    var originalImage = null;
    var strokes = [];
    var currentStroke = null;
    var isDragging = false;
    var editorMode = 'draw';
    var drawColor = '#e53935';
    var drawWidth = 3;
    var editorIsReference = false;
    var editorReferenceFile = null;

    function renderStroke(ctx, stroke) {
      if (stroke.type === 'draw') {
        if (stroke.points.length < 2) return;
        ctx.save();
        ctx.strokeStyle = stroke.color;
        ctx.lineWidth = stroke.width;
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';
        ctx.beginPath();
        ctx.moveTo(stroke.points[0].x, stroke.points[0].y);
        for (var i = 1; i < stroke.points.length; i++) ctx.lineTo(stroke.points[i].x, stroke.points[i].y);
        ctx.stroke();
        ctx.restore();
      } else if (stroke.type === 'highlight') {
        var r = stroke.rect;
        if (!r || r.w < 2 || r.h < 2) return;
        ctx.save();
        ctx.globalAlpha = 0.38;
        ctx.fillStyle = stroke.color;
        ctx.fillRect(r.x, r.y, r.w, r.h);
        ctx.globalAlpha = 1;
        ctx.strokeStyle = stroke.color;
        ctx.lineWidth = 1.5;
        ctx.strokeRect(r.x + 0.5, r.y + 0.5, r.w, r.h);
        ctx.restore();
      }
    }

    function drawEditorCanvas() {
      if (!editorCanvas || !originalImage) return;
      var ctx = editorCanvas.getContext('2d');
      ctx.clearRect(0, 0, editorCanvas.width, editorCanvas.height);
      ctx.drawImage(originalImage, 0, 0, editorCanvas.width, editorCanvas.height);
      strokes.forEach(function (s) { renderStroke(ctx, s); });
      if (currentStroke) renderStroke(ctx, currentStroke);
    }

    function setupEditorCanvas() {
      if (!originalImage || !editorCanvas) return;
      var maxW = editorHost.clientWidth || 600;
      var maxH = editorHost.clientHeight || 400;
      var scale = Math.min(maxW / originalImage.naturalWidth, maxH / originalImage.naturalHeight, 1);
      editorCanvas.width = Math.max(1, Math.round(originalImage.naturalWidth * scale));
      editorCanvas.height = Math.max(1, Math.round(originalImage.naturalHeight * scale));
      strokes = [];
      drawEditorCanvas();
    }

    function getCanvasPoint(e) {
      var rect = editorCanvas.getBoundingClientRect();
      var scaleX = editorCanvas.width / rect.width;
      var scaleY = editorCanvas.height / rect.height;
      var src = e.touches ? e.touches[0] : e;
      return { x: (src.clientX - rect.left) * scaleX, y: (src.clientY - rect.top) * scaleY };
    }

    function onPointerDown(e) {
      e.preventDefault();
      isDragging = true;
      var pt = getCanvasPoint(e);
      if (editorMode === 'draw') {
        currentStroke = { type: 'draw', color: drawColor, width: drawWidth, points: [pt] };
      } else {
        currentStroke = { type: 'highlight', color: drawColor, startPt: pt, rect: { x: pt.x, y: pt.y, w: 0, h: 0 } };
      }
    }

    function onPointerMove(e) {
      if (!isDragging || !currentStroke) return;
      e.preventDefault();
      var pt = getCanvasPoint(e);
      if (currentStroke.type === 'draw') {
        currentStroke.points.push(pt);
      } else {
        var sp = currentStroke.startPt;
        currentStroke.rect = { x: Math.min(pt.x, sp.x), y: Math.min(pt.y, sp.y), w: Math.abs(pt.x - sp.x), h: Math.abs(pt.y - sp.y) };
      }
      drawEditorCanvas();
    }

    function onPointerUp() {
      if (!isDragging || !currentStroke) return;
      isDragging = false;
      var skip = (currentStroke.type === 'draw' && currentStroke.points.length < 2) ||
                 (currentStroke.type === 'highlight' && (currentStroke.rect.w < 5 || currentStroke.rect.h < 5));
      if (!skip) strokes.push(currentStroke);
      currentStroke = null;
      drawEditorCanvas();
    }

    function syncWidthGroupVisibility() {
      if (widthGroup) widthGroup.style.display = editorMode === 'draw' ? '' : 'none';
    }

    function openEditor(itemId) {
      var item = items.find(function (entry) { return entry.id === itemId; });
      if (!item) return;
      var reader = new FileReader();
      reader.onload = function (ev) {
        editorCurrentItemId = itemId;
        editorImageType = item.file.type || 'image/jpeg';
        strokes = [];
        currentStroke = null;
        isDragging = false;
        var img = new Image();
        img.onload = function () {
          originalImage = img;
          editorHost.innerHTML = '';
          editorCanvas = document.createElement('canvas');
          editorCanvas.style.cursor = 'crosshair';
          editorCanvas.style.touchAction = 'none';
          editorHost.appendChild(editorCanvas);
          editorModal.hidden = false;
          requestAnimationFrame(function () {
            setupEditorCanvas();
            editorCanvas.addEventListener('mousedown', onPointerDown);
            editorCanvas.addEventListener('mousemove', onPointerMove);
            editorCanvas.addEventListener('mouseup', onPointerUp);
            editorCanvas.addEventListener('mouseleave', onPointerUp);
            editorCanvas.addEventListener('touchstart', onPointerDown, { passive: false });
            editorCanvas.addEventListener('touchmove', onPointerMove, { passive: false });
            editorCanvas.addEventListener('touchend', onPointerUp);
          });
        };
        img.src = ev.target.result;
      };
      reader.readAsDataURL(item.file);
    }

    function closeEditor() {
      editorModal.hidden = true;
      editorCurrentItemId = null;
      editorIsReference = false;
      editorReferenceFile = null;
      originalImage = null;
      editorCanvas = null;
      strokes = [];
      currentStroke = null;
      isDragging = false;
      editorHost.innerHTML = '';
    }

    function syncInput() {
      var dt = new DataTransfer();
      items.forEach(function (item) { dt.items.add(item.file); });
      input.files = dt.files;
    }

    function fileKey(file) {
      return [file.name, file.size, file.lastModified].join('::');
    }

    function removeItem(itemId) {
      items = items.filter(function (item) { return item.id !== itemId; });
      syncInput();
      renderPreviews();
    }

    function updateCountBadge() {
      var badge = document.getElementById('img-count-badge');
      if (!badge) return;
      if (!items.length) { badge.hidden = true; return; }
      badge.textContent = items.length + ' / ' + MAX_IMAGES + ' image' + (items.length !== 1 ? 's' : '') + ' added';
      badge.hidden = false;
      badge.className = 'img-count-badge' + (items.length >= MAX_IMAGES ? ' img-count-full' : '');
    }

    function renderPreviews() {
      grid.innerHTML = '';
      zone.classList.toggle('is-full', items.length >= MAX_IMAGES);
      if (!items.length) { grid.hidden = true; updateCountBadge(); return; }
      grid.hidden = false;
      updateCountBadge();

      items.forEach(function (item) {
        var reader = new FileReader();
        reader.onload = function (event) {
          var wrap = document.createElement('div');
          wrap.className = 'img-preview-item';

          var leftCol = document.createElement('div');
          leftCol.className = 'img-preview-left';

          var img = document.createElement('img');
          img.src = event.target.result;
          img.alt = item.file.name;

          var actionRow = document.createElement('div');
          actionRow.className = 'img-preview-actions';

          var editBtn = document.createElement('button');
          editBtn.type = 'button';
          editBtn.className = 'img-preview-action';
          editBtn.textContent = 'Mark up';
          editBtn.addEventListener('click', function () { openEditor(item.id); });

          var removeBtn = document.createElement('button');
          removeBtn.type = 'button';
          removeBtn.className = 'img-preview-action img-preview-action-danger';
          removeBtn.textContent = 'Remove';
          removeBtn.addEventListener('click', function () { removeItem(item.id); });

          actionRow.appendChild(editBtn);
          actionRow.appendChild(removeBtn);
          leftCol.appendChild(img);
          leftCol.appendChild(actionRow);

          var rightCol = document.createElement('div');
          rightCol.className = 'img-preview-right';

          var name = document.createElement('p');
          name.className = 'img-preview-name';
          name.textContent = item.file.name;

          var captionInput = document.createElement('textarea');
          captionInput.className = 'img-preview-caption';
          captionInput.placeholder = 'Add a note — e.g. "this is a similar piece I made"';
          captionInput.maxLength = 160;
          captionInput.value = item.caption;
          captionInput.rows = 3;

          var hiddenCaption = document.createElement('input');
          hiddenCaption.type = 'hidden';
          hiddenCaption.name = 'proposal_image_captions';
          hiddenCaption.value = item.caption;

          captionInput.addEventListener('input', function () {
            item.caption = captionInput.value;
            hiddenCaption.value = item.caption;
          });

          rightCol.appendChild(name);
          rightCol.appendChild(captionInput);
          rightCol.appendChild(hiddenCaption);
          wrap.appendChild(leftCol);
          wrap.appendChild(rightCol);
          grid.appendChild(wrap);
        };
        reader.readAsDataURL(item.file);
      });
    }

    function addFiles(newFiles) {
      var existing = new Set(items.map(function (item) { return fileKey(item.file); }));
      Array.from(newFiles).forEach(function (file) {
        if (items.length >= MAX_IMAGES) return;
        if (!file.type.startsWith('image/')) return;
        var key = fileKey(file);
        if (existing.has(key)) return;
        items.push({ id: nextId, file: file, caption: '' });
        nextId += 1;
        existing.add(key);
      });
      syncInput();
      renderPreviews();
    }

    input.addEventListener('change', function () { var selected = Array.from(this.files); this.value = ''; addFiles(selected); });
    zone.addEventListener('dragover', function (e) { e.preventDefault(); zone.classList.add('drag-over'); });
    zone.addEventListener('dragleave', function () { zone.classList.remove('drag-over'); });
    zone.addEventListener('drop', function (e) { e.preventDefault(); zone.classList.remove('drag-over'); addFiles(e.dataTransfer.files); });

    saveBtn.addEventListener('click', function () {
      if (!originalImage || !editorCanvas) return;
      if (!editorIsReference && editorCurrentItemId === null) return;

      var outCanvas = document.createElement('canvas');
      outCanvas.width = originalImage.naturalWidth;
      outCanvas.height = originalImage.naturalHeight;
      var outCtx = outCanvas.getContext('2d');
      outCtx.drawImage(originalImage, 0, 0);

      if (strokes.length) {
        var scaleX = originalImage.naturalWidth / editorCanvas.width;
        var scaleY = originalImage.naturalHeight / editorCanvas.height;
        outCtx.scale(scaleX, scaleY);
        strokes.forEach(function (s) { renderStroke(outCtx, s); });
      }

      var mimeType = editorImageType && editorImageType.startsWith('image/') ? editorImageType : 'image/jpeg';
      outCanvas.toBlob(function (blob) {
        if (!blob) return;
        var ext = mimeType === 'image/png' ? '.png' : (mimeType === 'image/webp' ? '.webp' : '.jpg');

        if (editorIsReference) {
          var refName = editorReferenceFile ? editorReferenceFile.name : 'reference';
          var rDot = refName.lastIndexOf('.');
          var rBase = rDot > 0 ? refName.slice(0, rDot) : refName;
          var newFile = new File([blob], rBase + '-annotated' + ext, { type: mimeType, lastModified: Date.now() });
          closeEditor();
          addFiles([newFile]);
        } else {
          var target = items.find(function (item) { return item.id === editorCurrentItemId; });
          if (!target) { closeEditor(); return; }
          var origName = target.file.name;
          var oDot = origName.lastIndexOf('.');
          var oBase = oDot > 0 ? origName.slice(0, oDot) : origName;
          var newFile2 = new File([blob], oBase + '-marked' + ext, { type: mimeType, lastModified: Date.now() });
          target.file = newFile2;
          syncInput();
          renderPreviews();
          closeEditor();
        }
      }, mimeType, mimeType === 'image/png' ? 1 : 0.92);
    });

    function openEditorFromUrl(url, suggestedName) {
      fetch(url)
        .then(function (resp) {
          if (!resp.ok) throw new Error('load failed');
          return resp.blob();
        })
        .then(function (blob) {
          var mimeType = blob.type || 'image/jpeg';
          var ext = mimeType === 'image/png' ? '.png' : (mimeType === 'image/webp' ? '.webp' : '.jpg');
          editorReferenceFile = new File([blob], (suggestedName || 'reference') + ext, { type: mimeType, lastModified: Date.now() });
          editorIsReference = true;
          editorImageType = mimeType;
          editorCurrentItemId = null;
          strokes = [];
          currentStroke = null;
          isDragging = false;

          var objectUrl = URL.createObjectURL(blob);
          var img = new Image();
          img.onload = function () {
            URL.revokeObjectURL(objectUrl);
            originalImage = img;
            editorHost.innerHTML = '';
            editorCanvas = document.createElement('canvas');
            editorCanvas.style.cursor = 'crosshair';
            editorCanvas.style.touchAction = 'none';
            editorHost.appendChild(editorCanvas);
            editorModal.hidden = false;
            requestAnimationFrame(function () {
              setupEditorCanvas();
              editorCanvas.addEventListener('mousedown', onPointerDown);
              editorCanvas.addEventListener('mousemove', onPointerMove);
              editorCanvas.addEventListener('mouseup', onPointerUp);
              editorCanvas.addEventListener('mouseleave', onPointerUp);
              editorCanvas.addEventListener('touchstart', onPointerDown, { passive: false });
              editorCanvas.addEventListener('touchmove', onPointerMove, { passive: false });
              editorCanvas.addEventListener('touchend', onPointerUp);
            });
          };
          img.onerror = function () { URL.revokeObjectURL(objectUrl); };
          img.src = objectUrl;
        })
        .catch(function () {});
    }

    document.querySelectorAll('.ref-img-slot-edit').forEach(function (btn) {
      btn.addEventListener('click', function () {
        openEditorFromUrl(btn.dataset.src, btn.dataset.name);
      });
    });

    if (undoBtn) undoBtn.addEventListener('click', function () { strokes.pop(); drawEditorCanvas(); });
    if (clearAllBtn) clearAllBtn.addEventListener('click', function () { strokes = []; drawEditorCanvas(); });

    if (modeDrawBtn) {
      modeDrawBtn.addEventListener('click', function () {
        editorMode = 'draw';
        modeDrawBtn.classList.add('is-active');
        if (modeHighlightBtn) modeHighlightBtn.classList.remove('is-active');
        syncWidthGroupVisibility();
      });
    }
    if (modeHighlightBtn) {
      modeHighlightBtn.addEventListener('click', function () {
        editorMode = 'highlight';
        modeHighlightBtn.classList.add('is-active');
        if (modeDrawBtn) modeDrawBtn.classList.remove('is-active');
        syncWidthGroupVisibility();
      });
    }
    if (widthThinBtn) {
      widthThinBtn.addEventListener('click', function () {
        drawWidth = 3;
        widthThinBtn.classList.add('is-active');
        if (widthThickBtn) widthThickBtn.classList.remove('is-active');
      });
    }
    if (widthThickBtn) {
      widthThickBtn.addEventListener('click', function () {
        drawWidth = 7;
        widthThickBtn.classList.add('is-active');
        if (widthThinBtn) widthThinBtn.classList.remove('is-active');
      });
    }
    if (colorGroup) {
      colorGroup.addEventListener('click', function (e) {
        var swatch = e.target.closest('.editor-color-swatch');
        if (!swatch) return;
        drawColor = swatch.dataset.color;
        colorGroup.querySelectorAll('.editor-color-swatch').forEach(function (s) {
          s.classList.toggle('is-active', s === swatch);
        });
      });
    }

    cancelBtn.addEventListener('click', closeEditor);
    editorCloseBtn.addEventListener('click', closeEditor);
    editorModal.addEventListener('click', function (e) { if (e.target === editorModal) closeEditor(); });
  })();

  // ── Reference image lightbox ───────────────────────────────────────────────
  (function () {
    var lightbox = document.getElementById('gallery-lightbox');
    var lbImg = document.getElementById('gallery-lightbox-img');
    var lbCaption = document.getElementById('gallery-lightbox-caption');
    var closeBtn = document.getElementById('gallery-lightbox-close');
    if (!lightbox) return;

    document.querySelectorAll('.proposal-preview-img-btn').forEach(function (btn) {
      btn.addEventListener('click', function () {
        lbImg.src = btn.dataset.src;
        lbImg.alt = btn.querySelector('img').alt;
        if (btn.dataset.caption) {
          lbCaption.textContent = btn.dataset.caption;
          lbCaption.hidden = false;
        } else {
          lbCaption.hidden = true;
        }
        lightbox.hidden = false;
        document.body.style.overflow = 'hidden';
      });
    });

    function closeLightbox() {
      lightbox.hidden = true;
      lbImg.src = '';
      document.body.style.overflow = '';
    }

    closeBtn.addEventListener('click', closeLightbox);
    lightbox.addEventListener('click', function (e) { if (e.target === lightbox) closeLightbox(); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && !lightbox.hidden) closeLightbox(); });
  })();

  // ── Double-submit protection ───────────────────────────────────────────────
  (function () {
    var form = document.querySelector('.request-form-card form');
    var submitBtn = form ? form.querySelector('button[type="submit"]') : null;
    if (!form || !submitBtn) return;
    var originalLabel = submitBtn.textContent;
    form.addEventListener('submit', function () {
      submitBtn.disabled = true;
      submitBtn.textContent = 'Submitting...';
      setTimeout(function () {
        submitBtn.disabled = false;
        submitBtn.textContent = originalLabel;
      }, 10000);
    });
  })();
})();
