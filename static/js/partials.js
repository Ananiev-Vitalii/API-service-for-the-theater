// --- helper: fetch HTML partials (actors/performances) ---
function fetchPartial(url, onOk) {
  if (!url) return;
  fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
    .then(r => (r.ok ? r.text() : Promise.reject(r)))
    .then(html => onOk(html))
    .catch(() => { /* optional: toast */ });
}

// --- navbar: active link + smooth scroll (supports /...#id and #id) ---
function initCustomAnchorScrollAndActive() {
  const nav = document.getElementById('mainNavbar');
  if (!nav) return;

  const entries = Array.from(nav.querySelectorAll('.nav-link[href*="#"]')).map(a => {
    const href = a.getAttribute('href') || '';
    const u = new URL(href, window.location.href);
    return {
      a,
      href,
      url: u,
      hash: u.hash || '',
      id: (u.hash || '').slice(1),
      isLocal: u.pathname === window.location.pathname
    };
  });

  if (!entries.length) return;

  const local = entries.filter(e => e.isLocal && e.id && document.getElementById(e.id));
  const sections = local.map(e => document.getElementById(e.id));

  function getNavbarHeight() {
    return nav.offsetHeight || 0;
  }

  function setActive(hash) {
    entries.forEach(e => e.a.classList.toggle('active', e.hash === hash));
  }

  function computeActive() {
    if (!sections.length) return;

    const navH = getNavbarHeight();
    const lineY = navH + 2;

    const atBottom = Math.abs((window.pageYOffset + window.innerHeight) - document.documentElement.scrollHeight) < 2;
    if (atBottom) {
      const last = local[local.length - 1];
      if (last) setActive(last.hash);
      return;
    }

    for (let i = 0; i < sections.length; i++) {
      const rect = sections[i].getBoundingClientRect();
      if (rect.top <= lineY && rect.bottom > lineY) {
        setActive(local[i].hash);
        return;
      }
    }

    let idx = 0;
    let minTop = Infinity;
    for (let i = 0; i < sections.length; i++) {
      const top = sections[i].getBoundingClientRect().top - navH - 1;
      if (top >= 0 && top < minTop) {
        minTop = top;
        idx = i;
      }
    }
    if (minTop === Infinity && local.length) idx = local.length - 1;
    setActive(local[idx]?.hash || '');
  }

  entries.forEach(e => {
    e.a.addEventListener('click', (ev) => {
      if (!e.isLocal || !e.id) return; // external/other page: allow default navigation

      const el = document.getElementById(e.id);
      if (!el) return;

      ev.preventDefault();

      const navH = getNavbarHeight();
      const desired = el.getBoundingClientRect().top + window.pageYOffset - navH;
      const maxScroll = document.documentElement.scrollHeight - window.innerHeight;
      const top = Math.max(0, Math.min(desired, maxScroll));

      window.scrollTo({ top, behavior: 'smooth' });
      setActive(e.hash);

      const collapseEl = document.getElementById('navbarNav');
      const bsCollapse = window.bootstrap?.Collapse?.getInstance?.(collapseEl);
      if (bsCollapse) bsCollapse.hide();
    });
  });

  let ticking = false;
  function onScrollOrResize() {
    if (!ticking) {
      ticking = true;
      window.requestAnimationFrame(() => {
        computeActive();
        ticking = false;
      });
    }
  }
  if (sections.length) {
    window.addEventListener('scroll', onScrollOrResize, { passive: true });
    window.addEventListener('resize', onScrollOrResize);
    setTimeout(computeActive, 0);
  }
}

// --- public init (called from template) ---
export function initPartials() {
  // Performances
  const allBtn   = document.getElementById('view-all-performances');
  const lessBtn  = document.getElementById('view-less-performances');
  const cardsDiv = document.getElementById('performances-cards');

  if (allBtn && lessBtn && cardsDiv) {
    const allUrl  = allBtn.dataset.url;
    const lessUrl = lessBtn.dataset.url;

    allBtn.addEventListener('click', (e) => {
      e.preventDefault();
      fetchPartial(allUrl, (html) => {
        cardsDiv.innerHTML = html;
        allBtn.style.display = 'none';
        lessBtn.style.display = '';
      });
    });

    lessBtn.addEventListener('click', (e) => {
      e.preventDefault();
      fetchPartial(lessUrl, (html) => {
        cardsDiv.innerHTML = html;
        lessBtn.style.display = 'none';
        allBtn.style.display = '';
        document.getElementById('performances')
          ?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      });
    });
  }

  // Actors
  const allActorsBtn  = document.getElementById('view-all-actors');
  const lessActorsBtn = document.getElementById('view-less-actors');
  const actorsDiv     = document.getElementById('actors-cards');

  if (allActorsBtn && lessActorsBtn && actorsDiv) {
    const allActorsUrl  = allActorsBtn.dataset.url;
    const lessActorsUrl = lessActorsBtn.dataset.url;

    allActorsBtn.addEventListener('click', (e) => {
      e.preventDefault();
      fetchPartial(allActorsUrl, (html) => {
        actorsDiv.innerHTML = html;
        allActorsBtn.style.display = 'none';
        lessActorsBtn.style.display = '';
      });
    });

    lessActorsBtn.addEventListener('click', (e) => {
      e.preventDefault();
      fetchPartial(lessActorsUrl, (html) => {
        actorsDiv.innerHTML = html;
        lessActorsBtn.style.display = 'none';
        allActorsBtn.style.display = '';
        document.getElementById('actors')
          ?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      });
    });
  }

  // Navbar behavior
  initCustomAnchorScrollAndActive();
}