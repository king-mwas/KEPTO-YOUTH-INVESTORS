/* KEPTO dashboard — self-contained balance-over-time chart (no external libs),
   W/M/Y toggle, profile-edit panel toggle, and avatar picker niceties. */
(function () {
  'use strict';

  // ---- profile edit panel ----
  var editToggle = document.getElementById('editToggle');
  var editPanel = document.getElementById('editPanel');
  if (editToggle && editPanel) {
    editToggle.addEventListener('click', function () {
      editPanel.hidden = !editPanel.hidden;
      if (!editPanel.hidden) editPanel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    });
    var cancel = document.getElementById('editCancel');
    if (cancel) cancel.addEventListener('click', function () { editPanel.hidden = true; });
  }

  // Choosing a preset clears an uploaded file, and vice-versa, so it's clear
  // which one wins.
  var fileInput = document.getElementById('avatarUpload');
  var presetRadios = document.querySelectorAll('input[name="avatar_preset"]');
  presetRadios.forEach(function (r) {
    r.addEventListener('change', function () { if (fileInput) fileInput.value = ''; });
  });
  if (fileInput) {
    fileInput.addEventListener('change', function () {
      if (fileInput.value) presetRadios.forEach(function (r) { r.checked = false; });
    });
  }

  // ---- chart ----
  var mount = document.getElementById('chartmount');
  var dataEl = document.getElementById('chart-data');
  if (!mount || !dataEl) return;

  var DATA;
  try { DATA = JSON.parse(dataEl.textContent); } catch (e) { return; }
  var goal = DATA.goal || 0;

  var W = 600, H = 200, padL = 10, padR = 14, padT = 18, padB = 26;

  function fmtK(n) {
    if (n >= 1000) return (n / 1000).toFixed(n % 1000 === 0 ? 0 : 1) + 'k';
    return String(Math.round(n));
  }

  function render(range) {
    var series = DATA[range] || [];
    var values = series.map(function (p) { return p.value; });
    var hasData = values.some(function (v) { return v > 0; });

    if (!series.length || !hasData) {
      mount.innerHTML = '<div class="chart-empty">No approved savings yet — your growth curve appears here after your first approved deposit.</div>';
      return;
    }

    var n = series.length;
    var maxV = Math.max.apply(null, values.concat([goal, 1])) * 1.12;
    var innerW = W - padL - padR, innerH = H - padT - padB;
    var baseY = H - padB;

    function x(i) { return n === 1 ? padL + innerW / 2 : padL + (i * innerW) / (n - 1); }
    function y(v) { return H - padB - (v / maxV) * innerH; }

    var linePts = series.map(function (p, i) { return x(i) + ',' + y(p.value); });
    var linePath = 'M' + linePts.join(' L');
    var areaPath = 'M' + x(0) + ',' + baseY + ' L' + linePts.join(' L') + ' L' + x(n - 1) + ',' + baseY + ' Z';

    // gridlines (3)
    var grid = '';
    for (var g = 1; g <= 3; g++) {
      var gy = padT + (innerH * g) / 4;
      grid += '<line x1="' + padL + '" y1="' + gy + '" x2="' + (W - padR) + '" y2="' + gy + '" class="grid"/>';
    }

    // goal target line
    var goalLine = '';
    if (goal > 0 && goal <= maxV) {
      var gyv = y(goal);
      goalLine = '<line x1="' + padL + '" y1="' + gyv + '" x2="' + (W - padR) + '" y2="' + gyv + '" class="goal-line"/>' +
        '<text x="' + (W - padR) + '" y="' + (gyv - 6) + '" class="goal-lbl" text-anchor="end">Goal ' + fmtK(goal) + '</text>';
    }

    // x labels (up to ~6, evenly)
    var step = Math.ceil(n / 6);
    var xlabels = '';
    for (var i = 0; i < n; i += step) {
      xlabels += '<text x="' + x(i) + '" y="' + (H - 8) + '" class="x-lbl" text-anchor="middle">' + series[i].label + '</text>';
    }

    var last = n - 1;
    var svg =
      '<svg class="chart" viewBox="0 0 ' + W + ' ' + H + '" preserveAspectRatio="none" role="img" aria-label="Account balance over time">' +
      '<defs><linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">' +
      '<stop offset="0%" stop-color="#2F6BFF" stop-opacity="0.28"/>' +
      '<stop offset="100%" stop-color="#2F6BFF" stop-opacity="0"/>' +
      '</linearGradient></defs>' +
      grid +
      '<path d="' + areaPath + '" fill="url(#areaGrad)"/>' +
      '<path d="' + linePath + '" class="line"/>' +
      goalLine +
      '<circle cx="' + x(last) + '" cy="' + y(series[last].value) + '" r="4.5" class="dot"/>' +
      xlabels +
      '</svg>';

    mount.innerHTML = svg;
  }

  var buttons = document.querySelectorAll('.toggle button[data-range]');
  buttons.forEach(function (b) {
    b.addEventListener('click', function () {
      buttons.forEach(function (o) { o.classList.remove('active'); });
      b.classList.add('active');
      render(b.getAttribute('data-range'));
    });
  });

  render('monthly');
})();
