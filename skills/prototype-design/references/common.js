(function () {
  var SHELL_COLLAPSED_KEY = 'ui-ref-sidebar-collapsed';
  var shell = document.querySelector('.app-shell');
  var toggleButtons = document.querySelectorAll('[data-sidebar-toggle]');
  var sidebar = document.querySelector('.sidebar');
  var wrappers = document.querySelectorAll('.select-wrap[data-select]');

  function applySidebarState(collapsed) {
    if (!shell) return;
    shell.classList.toggle('sidebar-collapsed', collapsed);
    toggleButtons.forEach(function (btn) {
      btn.setAttribute('aria-expanded', collapsed ? 'false' : 'true');
      btn.setAttribute('aria-label', collapsed ? '展开侧边栏' : '收起侧边栏');
      btn.setAttribute('title', collapsed ? '展开侧边栏' : '收起侧边栏');
    });
  }

  if (shell && sidebar && toggleButtons.length) {
    var stored = localStorage.getItem(SHELL_COLLAPSED_KEY);
    var isCollapsed = stored === '1';
    applySidebarState(isCollapsed);

    toggleButtons.forEach(function (btn) {
      btn.addEventListener('click', function () {
        isCollapsed = !shell.classList.contains('sidebar-collapsed');
        applySidebarState(isCollapsed);
        localStorage.setItem(SHELL_COLLAPSED_KEY, isCollapsed ? '1' : '0');
      });
    });
  }

  if (!wrappers.length) return;

  function closeAll(except) {
    wrappers.forEach(function (w) {
      if (w !== except) {
        w.classList.remove('is-open');
        var t = w.querySelector('.select-trigger');
        if (t) t.setAttribute('aria-expanded', 'false');
      }
    });
  }

  wrappers.forEach(function (wrap) {
    var trigger = wrap.querySelector('.select-trigger');
    var items = wrap.querySelectorAll('.select-item');
    if (!trigger || !items.length) return;

    trigger.addEventListener('click', function (e) {
      e.preventDefault();
      var opening = !wrap.classList.contains('is-open');
      closeAll(wrap);
      wrap.classList.toggle('is-open', opening);
      trigger.setAttribute('aria-expanded', opening ? 'true' : 'false');
    });

    trigger.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowDown' || e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        closeAll(wrap);
        wrap.classList.add('is-open');
        trigger.setAttribute('aria-expanded', 'true');
      }
      if (e.key === 'Escape') {
        wrap.classList.remove('is-open');
        trigger.setAttribute('aria-expanded', 'false');
      }
    });

    items.forEach(function (item) {
      item.addEventListener('click', function () {
        var value = item.getAttribute('data-value') || item.textContent.trim();
        var label = item.querySelector('.select-item-label');

        items.forEach(function (i) {
          i.classList.remove('is-selected');
          var check = i.querySelector('.select-check');
          if (check) check.hidden = true;
        });

        item.classList.add('is-selected');
        var activeCheck = item.querySelector('.select-check');
        if (activeCheck) activeCheck.hidden = false;

        trigger.textContent = label ? label.textContent.trim() : value;
        wrap.dataset.value = value;
        wrap.classList.remove('is-open');
        trigger.setAttribute('aria-expanded', 'false');
      });
    });
  });

  document.addEventListener('click', function (e) {
    var target = e.target;
    if (!(target instanceof Element)) return;
    var inside = target.closest('.select-wrap[data-select]');
    closeAll(inside || null);
    wrappers.forEach(function (w) {
      var t = w.querySelector('.select-trigger');
      if (t) t.setAttribute('aria-expanded', w.classList.contains('is-open') ? 'true' : 'false');
    });
  });

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
      closeAll(null);
      wrappers.forEach(function (w) {
        var t = w.querySelector('.select-trigger');
        if (t) t.setAttribute('aria-expanded', 'false');
      });
    }
  });
})();
