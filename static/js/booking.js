const DEFAULT_SUCCESS = 'Reservation successful! We will contact you by email shortly.';
const NO_PERFS_MSG    = 'No performances with available seats at the moment.';

function pickMessage(payload) {
  if (payload == null) return '';
  if (typeof payload === 'string') return payload.trim();
  if (typeof payload === 'object') {
    if (typeof payload.message === 'string' && payload.message.trim()) {
      return payload.message.trim();
    }
    const errs = payload.errors;
    if (errs && typeof errs === 'object') {
      const pieces = [];
      for (const val of Object.values(errs)) {
        if (Array.isArray(val)) {
          for (const item of val) {
            pieces.push(typeof item === 'string' ? item
              : (item && typeof item === 'object' && 'message' in item) ? String(item.message)
              : String(item));
          }
        } else if (typeof val === 'string') {
          pieces.push(val);
        }
      }
      return pieces.join(' ');
    }
  }
  return '';
}

export function initBookingForm() {
  const perfSelect = document.getElementById('id_performance');
  const rowSelect  = document.getElementById('id_row');
  const seatSelect = document.getElementById('id_seat');
  const form       = document.getElementById('ticket-form');
  const alertBox   = document.getElementById('form-alert');
  const bookBtn    = document.getElementById('book-btn');
  const btnSpin    = bookBtn?.querySelector('.spinner-border');
  const btnLabel   = bookBtn?.querySelector('.btn-label');

  if (!form || !perfSelect || !rowSelect || !seatSelect || !alertBox) return;

  let rowsCount = 0, seatsPerRow = 0, taken = [];

  // --- helper: refresh "My Reservations" table after success ---
  function refreshMyReservations() {
    const tbody = document.getElementById('my-reservations-body');
    const url = tbody?.dataset?.url;
    if (!tbody || !url) return;
    fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
      .then(r => r.ok ? r.text() : Promise.reject(r))
      .then(html => { tbody.innerHTML = html; })
      .catch(() => {});
  }

  // ---- helpers (UI) ----
  function hideAlert() {
    alertBox.classList.add('d-none');
    alertBox.textContent = '';
    alertBox.classList.remove('alert-success', 'alert-danger');
  }
  function showAlert(kind, msg) {
    alertBox.classList.remove('d-none', 'alert-success', 'alert-danger');
    alertBox.classList.add(kind === 'success' ? 'alert-success' : 'alert-danger');
    alertBox.textContent = (msg && String(msg).trim()) || (kind === 'success' ? DEFAULT_SUCCESS : '');
    alertBox.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }
  function setLoading(v) {
    if (!bookBtn) return;
    bookBtn.disabled = v;
    btnSpin?.classList.toggle('d-none', !v);
    if (btnLabel) btnLabel.style.opacity = v ? 0.75 : 1;
  }
  function disableControls() {
    rowSelect.innerHTML = '';
    seatSelect.innerHTML = '';
    rowSelect.disabled = true;
    seatSelect.disabled = true;
    if (bookBtn) bookBtn.disabled = true;
  }
  function enableControls() {
    rowSelect.disabled = false;
    seatSelect.disabled = false;
    if (bookBtn) bookBtn.disabled = false;
  }
  function ensurePlaceholder() {
    let first = perfSelect.options[0];
    if (!first || first.value !== '') {
      const ph = document.createElement('option');
      ph.value = '';
      ph.textContent = 'Select performance';
      ph.disabled = true;
      ph.selected = !perfSelect.value;
      perfSelect.insertBefore(ph, perfSelect.firstChild);
    } else {
      first.disabled = true;
      if (!perfSelect.value) first.selected = true;
    }
  }
  function removeCurrentPerformanceOption() {
    const idx = perfSelect.selectedIndex;
    if (idx >= 0) perfSelect.remove(idx);
  }
  function selectFirstAvailablePerformance() {
    for (let i = 0; i < perfSelect.options.length; i++) {
      const opt = perfSelect.options[i];
      if (opt.value) { perfSelect.selectedIndex = i; return opt.value; }
    }
    perfSelect.value = '';
    ensurePlaceholder();
    return '';
  }

  // ---- seats/rows builders ----
  function mapTakenByRow() {
    const m = new Map();
    for (const {row, seat} of taken) {
      if (!m.has(row)) m.set(row, new Set());
      m.get(row).add(seat);
    }
    return m;
  }
  function buildRowOptions(preserve = true) {
    const prev = parseInt(rowSelect.value || '0', 10) || 0;
    rowSelect.innerHTML = '';
    const byRow = mapTakenByRow();
    const freeRows = [];
    for (let r = 1; r <= rowsCount; r++) {
      const takenCnt = (byRow.get(r)?.size) || 0;
      if (takenCnt < seatsPerRow) freeRows.push(r);
    }
    if (!freeRows.length) return false;
    for (const r of freeRows) {
      const opt = document.createElement('option'); opt.value = r; opt.textContent = r;
      rowSelect.appendChild(opt);
    }
    rowSelect.value = String((preserve && freeRows.includes(prev)) ? prev : freeRows[0]);
    rowSelect.disabled = false;
    return true;
  }
  function buildSeatOptions() {
    seatSelect.innerHTML = '';
    const currentRow = parseInt(rowSelect.value || '0', 10) || 0;
    if (!currentRow) { seatSelect.disabled = true; return false; }
    const takenSeats = new Set(taken.filter(x => x.row === currentRow).map(x => x.seat));
    const freeSeats = [];
    for (let s = 1; s <= seatsPerRow; s++) if (!takenSeats.has(s)) freeSeats.push(s);
    if (!freeSeats.length) { seatSelect.disabled = true; return false; }
    for (const s of freeSeats) {
      const opt = document.createElement('option'); opt.value = s; opt.textContent = s;
      seatSelect.appendChild(opt);
    }
    seatSelect.value = String(freeSeats[0]);
    seatSelect.disabled = false;
    if (bookBtn) bookBtn.disabled = false;
    return true;
  }

  // ---- load hall data ----
  function loadHallData(perfId, { keepAlert = false, autoSwitch = true } = {}) {
    if (!perfId) { disableControls(); return; }
    const url = `/api/performance-info/${perfId}/`;

    fetch(url, {
      headers: {
        'X-Requested-With': 'XMLHttpRequest',
        'Accept': 'application/json'
      }
    })
    .then(async (r) => {
      if (!r.ok) {
        const txt = await r.text().catch(() => '');
        throw new Error(`HTTP ${r.status} ${r.statusText} ${txt.slice(0,200)}`);
      }
      return r.json();
    })
    .then(d => {
      rowsCount   = Number(d.rows) || 0;
      seatsPerRow = Number(d.seats_in_row) || 0;
      taken       = Array.isArray(d.taken) ? d.taken : [];
      const soldOut = !!d.sold_out || !rowsCount || !seatsPerRow;

      if (soldOut) {
        removeCurrentPerformanceOption();
        ensurePlaceholder();
        const nextId = autoSwitch ? selectFirstAvailablePerformance() : '';
        if (nextId) {
          if (!keepAlert) hideAlert();
          loadHallData(nextId, { keepAlert, autoSwitch });
        } else {
          disableControls();
          showAlert('error', NO_PERFS_MSG);
        }
        return;
      }

      if (!keepAlert) hideAlert();
      const hasRows  = buildRowOptions(true);
      const hasSeats = hasRows && buildSeatOptions();
      if (!hasRows || !hasSeats) {
        removeCurrentPerformanceOption();
        ensurePlaceholder();
        const nextId = autoSwitch ? selectFirstAvailablePerformance() : '';
        if (nextId) {
          loadHallData(nextId, { keepAlert, autoSwitch });
        } else {
          disableControls();
          showAlert('error', NO_PERFS_MSG);
        }
        return;
      }
      enableControls();
    })
    .catch(err => {
      console.error('performance-info failed:', err);
      disableControls();
      if (!keepAlert) showAlert('error', 'Failed to load hall data. Please try again.');
    });
  }

  // ---- init ----
  ensurePlaceholder();
  if (!perfSelect.value) {
    disableControls();
  } else {
    loadHallData(perfSelect.value, { keepAlert: false, autoSwitch: false });
  }

  perfSelect.addEventListener('change', () => {
    hideAlert();
    if (perfSelect.value) {
      loadHallData(perfSelect.value, { keepAlert: false, autoSwitch: false });
    } else {
      disableControls();
      ensurePlaceholder();
    }
  });

  rowSelect.addEventListener('change', () => {
    hideAlert();
    buildSeatOptions();
  });

  // ---- submit ----
  form.addEventListener('submit', (e) => {
    e.preventDefault();
    hideAlert();
    if (!perfSelect.value) { showAlert('error', 'Please select a performance first.'); return; }

    setLoading(true);
    const formData = new FormData(form);

    fetch(form.getAttribute('action') || window.location.href, {
      method: 'POST',
      body: formData,
      headers: { 'X-Requested-With': 'XMLHttpRequest', 'Accept': 'application/json' }
    })
    .then(async (res) => {
      if (res.redirected) { window.location = res.url; return; }
      const ctype = res.headers.get('Content-Type') || '';
      let payload = null;
      if (ctype.includes('application/json')) {
        payload = await res.json().catch(() => ({}));
      } else {
        const txt = await res.text().catch(() => '');
        payload = txt || {};
      }

      if (res.ok && payload && payload.success) {
        showAlert('success', pickMessage(payload) || DEFAULT_SUCCESS);
        if (perfSelect.value) {
          loadHallData(perfSelect.value, { keepAlert: true, autoSwitch: true });
        }
        refreshMyReservations();
      } else {
        const msg = pickMessage(payload) || 'Please fix the form errors and try again.';
        showAlert('error', msg);
        if (res.status === 409 && perfSelect.value) {
          loadHallData(perfSelect.value, { keepAlert: true, autoSwitch: true });
        }
      }
    })
    .catch(() => showAlert('error', 'Submission failed. Please try again.'))
    .finally(() => setLoading(false));
  });
}