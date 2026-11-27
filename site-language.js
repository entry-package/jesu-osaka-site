/* Headed by the site's existing accessible menu controls. */
(() => {
  'use strict';
  document.addEventListener('submit', event => {
    if (event.target.matches('form[data-preview-form]')) {
      event.preventDefault();
      event.stopImmediatePropagation();
    }
  }, true);
  const details = document.querySelector('.site-header .mobile-menu');
  const toggle = document.querySelector('.site-header .menu-toggle');
  const nav = details?.querySelector('nav') ?? document.querySelector('.site-header #site-nav');
  const opener = details?.querySelector('summary') ?? toggle;
  if (!nav || !opener) return;
  if (details) {
    details.addEventListener('toggle', () => { if (details.open) nav.scrollTop = 0; });
    matchMedia('(min-width: 961px)').addEventListener('change', ({matches}) => {
      if (matches) details.open = false;
    });
  } else {
    toggle.addEventListener('click', () => {
      if (toggle.getAttribute('aria-expanded') === 'true') nav.scrollTop = 0;
    });
  }
  nav.addEventListener('keydown', event => {
    if (opener.getClientRects().length === 0) return;
    if (!['ArrowDown', 'ArrowUp', 'Home', 'End'].includes(event.key)) return;
    const items = Array.from(nav.querySelectorAll('a[href]'));
    const index = items.indexOf(document.activeElement);
    if (index === -1) return;
    const next = event.key === 'Home' ? 0
      : event.key === 'End' ? items.length - 1
      : (index + (event.key === 'ArrowDown' ? 1 : -1) + items.length) % items.length;
    event.preventDefault();
    items[next].focus();
  });
})();
