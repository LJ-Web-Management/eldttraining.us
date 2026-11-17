// eldttraining.us — site interactions (no content depends on JS)
(function () {
  var track = function () { if (typeof window.gtag === 'function') { try { window.gtag.apply(null, arguments); } catch (e) {} } };

  document.addEventListener('DOMContentLoaded', function () {
    // Mobile nav
    var navToggle = document.getElementById('navToggle');
    var mainNav = document.getElementById('mainNav');
    if (navToggle && mainNav && !navToggle.dataset.navWired) {
      navToggle.dataset.navWired = '1';
      navToggle.addEventListener('click', function () {
        var isOpen = mainNav.classList.toggle('open');
        navToggle.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
      });
    }

    // State picker <select> → /pages/state/xx
    var sel = document.getElementById('statePicker');
    if (sel) {
      sel.addEventListener('change', function () { if (sel.value) window.location.href = sel.value; });
    }

    // GA4 ecommerce: view_item on course pages (data from JSON in page)
    var vi = document.getElementById('ga-view-item');
    if (vi) {
      try {
        var item = JSON.parse(vi.textContent);
        track('event', 'view_item', { currency: 'USD', value: item.price, items: [item] });
      } catch (e) {}
    }

    // GA4 view_item_list on course listing grids
    var grid = document.querySelector('[data-item-list]');
    if (grid) {
      var items = [];
      grid.querySelectorAll('[data-sku]').forEach(function (el, i) {
        items.push({ item_id: el.dataset.sku, item_name: el.dataset.name, price: parseFloat(el.dataset.price), index: i, item_brand: 'ELDT Training' });
      });
      if (items.length) track('event', 'view_item_list', { item_list_name: grid.dataset.itemList, items: items });
    }

    // Click tracking: enroll buttons, phone, email
    document.addEventListener('click', function (e) {
      var a = e.target.closest ? e.target.closest('a') : null;
      if (!a) return;
      var href = a.getAttribute('href') || '';
      if (href.indexOf('/checkout') === 0) {
        var m = href.match(/item=([^&]+)/);
        track('event', 'select_item', { item_list_name: document.title, items: [{ item_id: m ? decodeURIComponent(m[1]) : 'unknown' }] });
        track('event', 'enroll_click', { course: m ? decodeURIComponent(m[1]) : 'unknown', page_path: location.pathname });
      } else if (href.indexOf('tel:') === 0) {
        track('event', 'phone_click', { page_path: location.pathname });
        track('event', 'generate_lead', { method: 'phone' });
      } else if (href.indexOf('mailto:') === 0) {
        track('event', 'email_click', { page_path: location.pathname });
        track('event', 'generate_lead', { method: 'email' });
      }
    });

    // Video engagement
    var v = document.querySelector('video[data-track]');
    if (v) {
      var started = false;
      v.addEventListener('play', function () { if (!started) { started = true; track('event', 'video_start', { video_title: v.dataset.track }); } });
      v.addEventListener('ended', function () { track('event', 'video_complete', { video_title: v.dataset.track }); });
    }
  });
})();
