function fetchPartial(url, onOk) {
  if (!url) return;
  fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
    .then(r => r.ok ? r.text() : Promise.reject(r))
    .then(html => onOk(html))
    .catch(() => {});
}

export function initPartials() {
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

  if (window.bootstrap?.ScrollSpy) {
    new bootstrap.ScrollSpy(document.body, { target: '#mainNavbar' });
  }
}