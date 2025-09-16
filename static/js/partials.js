// --- small helper to fetch HTML partials (actors/performances) ---
function fetchPartial(url, onOk) {
  if (!url) return;
  fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
    .then(r => (r.ok ? r.text() : Promise.reject(r)))
    .then(html => onOk(html))
    .catch(() => { /* optionally show a toast */ });
}

// --- navbar active handling (robust alternative to ScrollSpy) ---
function initCustomAnchorScrollAndActive() {
  const nav = document.getElementById('mainNavbar');
  if (!nav) return;

  // links like <a href="#section-id">
  const links = Array.from(nav.querySelectorAll('.nav-link[href^="#"]'))
    .filter(a => !!document.getElementById(a.getAttribute('href').slice(1)));

  if (!links.length) return;

  const sections = links.map(a => document.getElementById(a.getAttribute('href').slice(1)));

  function getNavbarHeight() {
    return nav.offsetHeight || 0;
  }

  function setActive(hash) {
    links.forEach(a => a.classList.toggle('active', a.getAttribute('href') === hash));
  }

  // Choose section intersecting a horizontal line just under the navbar.
  function computeActive() {
    const navH = getNavbarHeight();
    const lineY = navH + 2;

    const atBottom =
      Math.abs((window.pageYOffset + window.innerHeight) - document.documentElement.scrollHeight) < 2;
    if (atBottom && sections.length) {
      const last = links[sections.length - 1]?.getAttribute('href');
      if (last) setActive(last);
      return;
    }

    for (let i = 0; i < sections.length; i++) {
      const rect = sections[i].getBoundingClientRect();
      if (rect.top <= lineY && rect.bottom > lineY) {
        const hash = links[i].getAttribute('href');
        if (hash) setActive(hash);
        return;
      }
    }

    // Fallback: nearest visible from top; or last if none
    let activeIdx = 0;
    let minTop = Infinity;
    for (let i = 0; i < sections.length; i++) {
      const top = sections[i].getBoundingClientRect().top - navH - 1;
      if (top >= 0 && top < minTop) {
        minTop = top;
        activeIdx = i;
      }
    }
    if (minTop === Infinity && sections.length) activeIdx = sections.length - 1;
    const hash = links[activeIdx]?.getAttribute('href');
    if (hash) setActive(hash);
  }

  // Smooth scroll with clamp, collapse close on mobile
  links.forEach(a => {
    a.addEventListener('click', (e) => {
      const hash = a.getAttribute('href');
      const id = hash?.slice(1);
      const el = id ? document.getElementById(id) : null;
      if (!el) return;

      e.preventDefault();

      const navH = getNavbarHeight();
      const desired = el.getBoundingClientRect().top + window.pageYOffset - navH;
      const maxScroll = document.documentElement.scrollHeight - window.innerHeight;
      const top = Math.max(0, Math.min(desired, maxScroll)); // clamp inside page

      window.scrollTo({ top, behavior: 'smooth' });
      setActive(hash);

      const collapseEl = document.getElementById('navbarNav');
      const bsCollapse = window.bootstrap?.Collapse?.getInstance?.(collapseEl);
      if (bsCollapse) bsCollapse.hide();
    });
  });

  // Throttled listeners
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
  window.addEventListener('scroll', onScrollOrResize, { passive: true });
  window.addEventListener('resize', onScrollOrResize);

  // Initial sync after layout
  setTimeout(computeActive, 0);
}

// --- public init used from template ---
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

  // Replace default ScrollSpy with robust custom logic
  initCustomAnchorScrollAndActive();
}