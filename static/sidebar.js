// sidebar.js
document.addEventListener('DOMContentLoaded', () => {
  const toggleBtn =
    document.querySelector('.menu-toggle') ||
    document.querySelector('.menu-icon') ||
    document.querySelector('.left-dots');

  const sideMenu = document.querySelector('.side-menu');
  let overlay = document.querySelector('.overlay');

  // Create overlay if missing
  if (!overlay) {
    overlay = document.createElement('div');
    overlay.className = 'overlay';
    document.body.appendChild(overlay);
  }

  // Helper guards
  const hasSide = Boolean(sideMenu);
  const hasToggle = Boolean(toggleBtn);

  // Open/close helpers
  function openSidebar() {
    if (!hasSide) return;
    sideMenu.classList.add('open');
    overlay.classList.add('show');
    // optional: prevent body scroll when sidebar open
    document.body.style.overflow = 'hidden';
  }

  function closeSidebar() {
    if (!hasSide) return;
    sideMenu.classList.remove('open');
    overlay.classList.remove('show');
    document.body.style.overflow = '';
  }

  // Toggle button
  if (hasToggle) {
    toggleBtn.addEventListener('click', (ev) => {
      ev.stopPropagation();
      if (!hasSide) return;
      sideMenu.classList.contains('open') ? closeSidebar() : openSidebar();
    });
  }

  // Overlay click closes sidebar
  overlay.addEventListener('click', () => {
    closeSidebar();
  });

  // Click outside closes sidebar
  document.addEventListener('click', (ev) => {
    if (!hasSide) return;
    if (!sideMenu.classList.contains('open')) return;
    const clickedInside = sideMenu.contains(ev.target) || (hasToggle && toggleBtn.contains(ev.target));
    if (!clickedInside) closeSidebar();
  });

  // --- Active sync logic ---
  const sideLinks = hasSide ? Array.from(sideMenu.querySelectorAll('a')) : [];
  const navLinks = Array.from(document.querySelectorAll('.second-navbar a'));

  // Derive a stable key for comparing links (data-category preferred)
  function getKeyFromLink(a) {
    if (!a) return '';
    const ds = a.dataset && a.dataset.category;
    if (ds) return String(ds).trim().toLowerCase();

    const href = a.getAttribute('href') || '';
    // If href is meaningful (not '#' or javascript void), use pathname end
    if (href && href !== '#' && !href.startsWith('javascript')) {
      try {
        const url = new URL(href, location.origin);
        let p = url.pathname || '';
        if (p.endsWith('/')) p = p.slice(0, -1);
        const parts = p.split('/');
        const last = parts.pop() || parts.pop() || '';
        if (last) return last.toLowerCase();
      } catch (e) {
        // ignore, fallback to text
      }
    }

    const txt = (a.textContent || a.innerText || '').trim().toLowerCase();
    // map common labels
    if (txt === 'home') return 'general';
    return txt;
  }

  function setActiveByKey(key) {
    if (!key) return;
    sideLinks.forEach(l => l.classList.toggle('active', getKeyFromLink(l) === key));
    navLinks.forEach(l => l.classList.toggle('active', getKeyFromLink(l) === key));
    try { localStorage.setItem('selectedCategory', key); } catch (e) {}
  }

  // Click handlers for sidebar links (do NOT prevent default so existing onclick handlers still run)
  sideLinks.forEach(link => {
    link.addEventListener('click', (ev) => {
      const key = getKeyFromLink(link);
      setActiveByKey(key);
      // close sidebar after selection
      closeSidebar();
      // allow default behavior (so if inline onclick exists, it runs)
    });
  });

  // Click handlers for navbar links (sync back to sidebar)
  navLinks.forEach(link => {
    link.addEventListener('click', (ev) => {
      const key = getKeyFromLink(link);
      setActiveByKey(key);
      // do NOT close sidebar here (user clicked top nav)
    });
  });

  // Restore active from localStorage on load (or pick a sensible default)
  const saved = (() => {
    try { return localStorage.getItem('selectedCategory'); } catch (e) { return null; }
  })();

  if (saved) {
    setActiveByKey(saved);
  } else if (navLinks.length) {
    // default to first nav link
    setActiveByKey(getKeyFromLink(navLinks[0]));
  }
});
