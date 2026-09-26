'use strict';

(() => {
  const $ = selector => document.querySelector(selector);
  const songs = Array.isArray(window.SONGBOOK_DATA) ? window.SONGBOOK_DATA : [];
  const layers = ['original', 'pronunciation', 'translation'];
  const storageKey = 'han-sojeol-reader-v2';
  let preferences = {};
  try { preferences = JSON.parse(localStorage.getItem(storageKey) || '{}') || {}; } catch { /* Reading also works without storage. */ }
  let size = Number.isFinite(preferences.size) ? Math.max(12, Math.min(28, preferences.size)) : 16;
  const visible = Object.fromEntries(layers.map(layer => [layer, preferences.visible?.[layer] !== false]));
  if (!Object.values(visible).some(Boolean)) layers.forEach(layer => { visible[layer] = true; });
  let currentId;

  function savePreferences() {
    try { localStorage.setItem(storageKey, JSON.stringify({size, visible, currentId})); } catch { /* Optional device preferences. */ }
  }

  function updateView() {
    document.documentElement.style.setProperty('--lyric-size', `${size}px`);
    $('#font-size').textContent = `${size}px`;
    $('#smaller').disabled = size <= 12;
    $('#larger').disabled = size >= 28;
    for (const layer of layers) {
      $(`[data-layer="${layer}"]`).checked = visible[layer];
      $('#lyrics').classList.toggle(`hide-${layer}`, !visible[layer]);
    }
  }

  function hashSong() {
    try {
      const id = decodeURIComponent(location.hash.slice(1));
      return songs.find(song => song.id === id);
    } catch { return undefined; }
  }

  function renderSong(id, moveToTop = false) {
    const index = songs.findIndex(song => song.id === id);
    if (index < 0) return;
    const song = songs[index];
    currentId = id;
    $('#song-select').value = id;
    $('#song-title').textContent = song.title;
    $('#song-vocal').textContent = song.vocal;
    $('#song-album').textContent = `HOPEFUL FE@THERS · ${song.albumName} · ${String(song.trackNumber).padStart(2, '0')}`;
    $('#song-position').textContent = `${index + 1} / ${songs.length}`;
    document.title = `${song.title} · 한 소절`;
    const fragment = document.createDocumentFragment();
    for (const stanza of song.stanzas) {
      const block = document.createElement('div');
      block.className = 'stanza';
      for (const line of stanza.lines) {
        const group = document.createElement('div');
        group.className = 'lyric-line';
        for (const layer of layers) {
          const text = document.createElement('p');
          text.className = `lyric-text ${layer}`;
          text.lang = layer === 'original' ? 'ja' : 'ko';
          text.textContent = line[layer];
          group.append(text);
        }
        block.append(group);
      }
      fragment.append(block);
    }
    $('#lyrics').replaceChildren(fragment);
    for (const [selector, target] of [['#previous-song', songs[index - 1]], ['#next-song', songs[index + 1]]]) {
      const link = $(selector);
      link.hidden = !target;
      if (target) { link.href = `#${target.id}`; link.title = target.title; }
      else { link.removeAttribute('href'); link.removeAttribute('title'); }
    }
    $('#status').textContent = `${song.title}, ${song.vocal}`;
    savePreferences();
    if (moveToTop) window.scrollTo({top: 0, behavior: 'instant'});
  }

  if (!songs.length) { $('#load-error').hidden = false; return; }
  $('#song-select').replaceChildren();
  const groups = new Map();
  for (const song of songs) {
    if (!groups.has(song.albumId)) {
      const group = document.createElement('optgroup');
      group.label = song.albumName;
      groups.set(song.albumId, group);
      $('#song-select').append(group);
    }
    const option = document.createElement('option');
    option.value = song.id;
    option.textContent = `${String(song.trackNumber).padStart(2, '0')}. ${song.title} — ${song.vocal}`;
    groups.get(song.albumId).append(option);
  }
  $('#song-select').disabled = false;
  $('#song-select').addEventListener('change', event => { location.hash = event.target.value; });
  window.addEventListener('hashchange', () => {
    const song = hashSong();
    if (song) renderSong(song.id, true);
  });
  for (const layer of layers) {
    $(`[data-layer="${layer}"]`).addEventListener('change', event => {
      if (!event.target.checked && Object.values(visible).filter(Boolean).length === 1) {
        event.target.checked = true;
        $('#status').textContent = '최소 한 가지 가사는 표시해 주세요.';
        return;
      }
      visible[layer] = event.target.checked;
      updateView(); savePreferences();
    });
  }
  $('#smaller').addEventListener('click', () => { size = Math.max(12, size - 1); updateView(); savePreferences(); });
  $('#larger').addEventListener('click', () => { size = Math.min(28, size + 1); updateView(); savePreferences(); });
  $('#back-to-top').addEventListener('click', event => { event.preventDefault(); window.scrollTo({top: 0, behavior: 'instant'}); });
  const initial = hashSong() || songs.find(song => song.id === preferences.currentId) || songs[0];
  updateView();
  renderSong(initial.id);
  try { history.replaceState(null, '', `#${initial.id}`); } catch { /* File viewers may restrict history changes. */ }
})();
