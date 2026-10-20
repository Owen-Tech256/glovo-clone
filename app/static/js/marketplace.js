// Progressive enhancement only. Security and business rules remain server-side.
(function () {
  'use strict';

  var ZONE_KEY = 'mp.deliveryArea';

  function storageGet(key) {
    try { return window.localStorage.getItem(key); } catch (e) { return null; }
  }
  function storageSet(key, value) {
    try { window.localStorage.setItem(key, value); } catch (e) { /* storage unavailable: choice lasts for this page only */ }
  }

  // Confirm dialogs for sensitive forms.
  function initConfirm() {
    document.querySelectorAll('[data-confirm]').forEach(function (form) {
      form.addEventListener('submit', function (event) {
        if (!window.confirm(form.dataset.confirm || 'Are you sure?')) event.preventDefault();
      });
    });
  }

  // Stop double submissions and show a loading state.
  function initSubmitOnce() {
    document.querySelectorAll('form[data-submit-once]').forEach(function (form) {
      form.addEventListener('submit', function () {
        var button = form.querySelector('button[type="submit"]');
        if (!button || button.disabled) return;
        window.setTimeout(function () {
          button.disabled = true;
          button.dataset.label = button.textContent;
          button.textContent = 'Adding...';
          form.classList.add('is-loading');
        }, 0);
      });
    });
    window.addEventListener('pageshow', function (event) {
      if (!event.persisted) return;
      document.querySelectorAll('form[data-submit-once].is-loading').forEach(function (form) {
        var button = form.querySelector('button[type="submit"]');
        form.classList.remove('is-loading');
        if (button) { button.disabled = false; button.textContent = button.dataset.label || 'Add to cart'; }
      });
    });
  }

  // Dropdown menus (<details data-menu>): one open at a time, close on outside click or Escape.
  function initMenus() {
    var menus = Array.prototype.slice.call(document.querySelectorAll('details[data-menu]'));
    menus.forEach(function (menu) {
      menu.addEventListener('toggle', function () {
        if (!menu.open) return;
        menus.forEach(function (other) { if (other !== menu) other.open = false; });
      });
    });
    document.addEventListener('click', function (event) {
      menus.forEach(function (menu) { if (menu.open && !menu.contains(event.target)) menu.open = false; });
    });
    document.addEventListener('keydown', function (event) {
      if (event.key !== 'Escape') return;
      menus.forEach(function (menu) {
        if (!menu.open) return;
        menu.open = false;
        var summary = menu.querySelector('summary');
        if (summary) summary.focus();
      });
    });
  }

  // Delivery area: a per-browser convenience only. It does not validate addresses or change prices.
  function initLocation() {
    var labels = document.querySelectorAll('[data-location-label]');
    var buttons = document.querySelectorAll('[data-zone]');
    var selects = document.querySelectorAll('[data-zone-select]');
    if (!labels.length && !selects.length) return;

    function apply(zone) {
      labels.forEach(function (el) { el.textContent = zone || 'Choose area'; });
      buttons.forEach(function (btn) {
        var on = zone && btn.dataset.zone === zone;
        btn.classList.toggle('is-selected', !!on);
        btn.setAttribute('aria-pressed', on ? 'true' : 'false');
      });
      selects.forEach(function (sel) { sel.value = zone || ''; });
    }

    var saved = storageGet(ZONE_KEY);
    var known = Array.prototype.some.call(buttons, function (b) { return b.dataset.zone === saved; });
    apply(known ? saved : '');

    buttons.forEach(function (btn) {
      btn.addEventListener('click', function () {
        storageSet(ZONE_KEY, btn.dataset.zone);
        apply(btn.dataset.zone);
        var menu = btn.closest('details');
        if (menu) menu.open = false;
      });
    });
    selects.forEach(function (sel) {
      sel.addEventListener('change', function () {
        storageSet(ZONE_KEY, sel.value);
        apply(sel.value);
      });
    });
  }

  // Search suggestions backed by the existing /api/catalog endpoint.
  function initSuggest() {
    var form = document.querySelector('form[data-suggest]');
    if (!form || !window.fetch) return;
    var input = form.querySelector('input[name="q"]');
    var box = form.querySelector('.suggest');
    var endpoint = form.dataset.endpoint;
    var productUrl = form.dataset.productUrl;
    var nilId = '00000000-0000-0000-0000-000000000000';
    var timer = null;
    var controller = null;
    var active = -1;

    function items() { return box.querySelectorAll('.suggest__item, .suggest__all'); }
    function close() {
      box.hidden = true;
      box.textContent = '';
      input.setAttribute('aria-expanded', 'false');
      active = -1;
    }
    function open() { box.hidden = false; input.setAttribute('aria-expanded', 'true'); }
    function status(text) {
      box.textContent = '';
      var p = document.createElement('p');
      p.className = 'suggest__status';
      p.setAttribute('role', 'status');
      p.textContent = text;
      box.appendChild(p);
      open();
    }
    function highlight(index) {
      var list = items();
      list.forEach(function (el, i) { el.setAttribute('aria-selected', i === index ? 'true' : 'false'); });
      active = index;
    }
    function render(data, query) {
      box.textContent = '';
      var results = (data && data.items) || [];
      if (!results.length) { status('No matching products. Press Enter to search stores and categories.'); return; }
      results.slice(0, 6).forEach(function (item, i) {
        var a = document.createElement('a');
        a.className = 'suggest__item';
        a.id = 'suggest-' + i;
        a.setAttribute('role', 'option');
        a.href = productUrl.replace(nilId, encodeURIComponent(item.id));
        var left = document.createElement('span');
        var name = document.createElement('span');
        name.className = 'suggest__name';
        name.textContent = item.name;
        var meta = document.createElement('span');
        meta.className = 'suggest__meta';
        meta.textContent = item.category + ' · ' + item.vendor + (item.stock_available ? '' : ' · Out of stock');
        left.appendChild(name);
        left.appendChild(meta);
        var price = document.createElement('span');
        price.className = 'suggest__price';
        price.textContent = 'UGX ' + Number(item.price_ugx).toLocaleString('en-US');
        a.appendChild(left);
        a.appendChild(price);
        box.appendChild(a);
      });
      var all = document.createElement('a');
      all.className = 'suggest__all';
      all.setAttribute('role', 'option');
      all.href = form.getAttribute('action') + '?q=' + encodeURIComponent(query);
      all.textContent = 'See all results for "' + query + '"';
      box.appendChild(all);
      open();
    }
    function search(query) {
      if (controller) controller.abort();
      controller = window.AbortController ? new AbortController() : null;
      status('Searching...');
      fetch(endpoint + '?q=' + encodeURIComponent(query), {
        headers: { Accept: 'application/json' },
        credentials: 'same-origin',
        signal: controller ? controller.signal : undefined
      }).then(function (response) {
        if (!response.ok) throw new Error('bad status');
        return response.json();
      }).then(function (data) {
        if (input.value.trim() === query) render(data, query);
      }).catch(function (error) {
        if (error && error.name === 'AbortError') return;
        status('Suggestions are unavailable. Press Enter to search.');
      });
    }

    input.addEventListener('input', function () {
      window.clearTimeout(timer);
      var query = input.value.trim();
      if (query.length < 2) { if (controller) controller.abort(); close(); return; }
      timer = window.setTimeout(function () { search(query); }, 220);
    });
    input.addEventListener('keydown', function (event) {
      var list = items();
      if (event.key === 'Escape') { close(); return; }
      if (box.hidden || !list.length) return;
      if (event.key === 'ArrowDown') { event.preventDefault(); highlight((active + 1) % list.length); }
      else if (event.key === 'ArrowUp') { event.preventDefault(); highlight((active - 1 + list.length) % list.length); }
      else if (event.key === 'Enter' && active >= 0) { event.preventDefault(); list[active].click(); }
    });
    document.addEventListener('click', function (event) { if (!form.contains(event.target)) close(); });
  }

  // Broken product images fall back to the placeholder tile (capture phase: error does not bubble).
  function initImageFallback() {
    document.addEventListener('error', function (event) {
      var img = event.target;
      if (!img || img.tagName !== 'IMG' || !img.hasAttribute('data-fallback')) return;
      img.hidden = true;
      var placeholder = img.parentNode && img.parentNode.querySelector('.media__placeholder');
      if (placeholder) placeholder.hidden = false;
    }, true);
  }

  function init() {
    initConfirm();
    initSubmitOnce();
    initMenus();
    initLocation();
    initSuggest();
    initImageFallback();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
