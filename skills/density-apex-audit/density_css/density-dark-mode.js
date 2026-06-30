/**
 * BMW Density Dark Mode Toggle
 * ─────────────────────────────────────────────────────────────────
 * Injects a "Dark Mode" toggle item into the APEX user menu
 * dropdown (the one triggered by the #USER# nav bar button).
 *
 * How it works:
 *   1. On page load, applies saved dark mode preference from localStorage
 *   2. Starts a MutationObserver immediately — does NOT wait for APEX JS
 *      to be ready, because in APEX v87+ the nav bar buttons are hydrated
 *      dynamically after DOMContentLoaded.
 *   3. When a button with [data-menu] appears in the header nav bar, hooks
 *      its click event AND watches for the menu div to become visible.
 *   4. On menu open: injects a Density toggle item with switch visual.
 *   5. Toggling adds/removes 'ds-dark' on <body>.
 *   6. Saves preference to localStorage so it persists across pages/sessions.
 *
 * Compatibility:
 *   - APEX Universal Theme v87+ (data-menu attribute, no data-menu-id)
 *   - APEX Universal Theme v83 and earlier (same data-menu attribute)
 *   - Both DOMContentLoaded and apex.jQuery ready paths covered
 *
 * Requires: density-dark-mode.css to be loaded for the token overrides.
 * ─────────────────────────────────────────────────────────────────
 */
(function () {
  'use strict';

  var STORAGE_KEY = 'ds-dark-mode';
  var BODY_CLASS  = 'ds-dark';
  var INJECTED_ID = 'ds-dark-mode-toggle-item';

  /* Tracks which menu IDs we have already hooked to avoid double-binding */
  var hookedMenuIds = {};

  /* ── 1. Apply saved preference immediately (before paint) ── */
  function applyPreference() {
    if (localStorage.getItem(STORAGE_KEY) === 'on') {
      document.body.classList.add(BODY_CLASS);
    } else {
      document.body.classList.remove(BODY_CLASS);
    }
  }

  /* ── 2. Toggle dark mode on/off ──────────────────────────── */
  function toggleDarkMode() {
    var isDark = document.body.classList.toggle(BODY_CLASS);
    localStorage.setItem(STORAGE_KEY, isDark ? 'on' : 'off');
    updateToggleVisual();
    syncDialogIframes(isDark);
  }

  /* ── 2b. Sync ds-dark into any open dialog iframes ──────── */
  function syncDialogIframes(isDark) {
    /*
     * APEX renders modal dialogs (Feedback, Help, About sub-pages)
     * as full HTML documents inside <iframe> elements embedded in
     * jQuery UI .ui-dialog containers. The parent window's dark-mode
     * toggle must propagate into those iframes so
     * density-dark-mode.css body.ds-dark.t-Dialog-page rules apply.
     *
     * We also apply the saved localStorage preference to any iframe
     * that loads while dark mode is already on (handled in
     * applyPreference via the iframe load event below).
     */
    var iframes = document.querySelectorAll('.ui-dialog iframe, [role="dialog"] iframe');
    for (var i = 0; i < iframes.length; i++) {
      try {
        var iframeDoc = iframes[i].contentDocument || iframes[i].contentWindow.document;
        if (!iframeDoc || !iframeDoc.body) continue;
        if (isDark) {
          iframeDoc.body.classList.add(BODY_CLASS);
        } else {
          iframeDoc.body.classList.remove(BODY_CLASS);
        }
      } catch (e) {
        /* Cross-origin iframe — cannot access. Skip silently. */
      }
    }
  }

  /* ── 2c. Apply dark mode to a newly opened dialog iframe ── */
  function watchDialogIframes() {
    /*
     * When a dialog opens AFTER dark mode is already enabled,
     * the iframe loads fresh with no ds-dark class. We watch for
     * new iframes appearing in .ui-dialog containers and apply the
     * preference on their load event.
     */
    var iframeObserver = new MutationObserver(function (mutations) {
      mutations.forEach(function (m) {
        m.addedNodes && Array.prototype.forEach.call(m.addedNodes, function (node) {
          if (node.tagName === 'IFRAME') {
            node.addEventListener('load', function () {
              var savedPref = localStorage.getItem(STORAGE_KEY);
              if (savedPref !== 'on') return;
              try {
                var doc = node.contentDocument || node.contentWindow.document;
                if (doc && doc.body) doc.body.classList.add(BODY_CLASS);
              } catch (e) { /* cross-origin */ }
            });
          }
          /* Also check for iframes inside added nodes */
          if (node.querySelectorAll) {
            var nested = node.querySelectorAll('iframe');
            nested && Array.prototype.forEach.call(nested, function (iframe) {
              iframe.addEventListener('load', function () {
                var savedPref = localStorage.getItem(STORAGE_KEY);
                if (savedPref !== 'on') return;
                try {
                  var doc = iframe.contentDocument || iframe.contentWindow.document;
                  if (doc && doc.body) doc.body.classList.add(BODY_CLASS);
                } catch (e) { /* cross-origin */ }
              });
            });
          }
        });
      });
    });

    iframeObserver.observe(document.body, {
      childList: true,
      subtree: true,
    });
  }

  /* ── 3. Update the toggle switch visual state ────────────── */
  function updateToggleVisual() {
    var item = document.getElementById(INJECTED_ID);
    if (!item) return;
    var sw = item.querySelector('.ds-dark-toggle-switch');
    if (sw) {
      sw.setAttribute('aria-checked',
        document.body.classList.contains(BODY_CLASS) ? 'true' : 'false');
    }
  }

  /* ── 4. Build the menu item HTML ─────────────────────────── */
  function buildToggleItem() {
    var li = document.createElement('li');
    li.id = INJECTED_ID;
    li.setAttribute('role', 'none');
    li.className = 'a-Menu-item';

    var isDark = document.body.classList.contains(BODY_CLASS);
    li.innerHTML = [
      '<div class="a-Menu-inner">',
        '<span class="a-Menu-labelContainer">',
          '<span class="a-Menu-statusCol"></span>',
          '<button type="button" role="menuitem" tabindex="0"',
            ' class="a-Menu-label" id="' + INJECTED_ID + 'i"',
            ' aria-label="Toggle dark mode"',
            ' style="display:flex;align-items:center;justify-content:space-between;',
                     'width:100%;background:none;border:none;cursor:pointer;',
                     'padding:0;font:inherit;color:inherit;">',
            '<span class="ds-dark-toggle-label-text">Dark Mode</span>',
            '<span class="ds-dark-toggle-switch"',
              ' role="switch" aria-checked="' + (isDark ? 'true' : 'false') + '"',
              ' aria-hidden="true"></span>',
          '</button>',
        '</span>',
        '<span class="a-Menu-accelContainer">',
          '<span class="a-Menu-subMenuCol"></span>',
        '</span>',
      '</div>',
    ].join('');

    li.addEventListener('click', function (e) {
      e.preventDefault();
      e.stopPropagation();
      toggleDarkMode();
    });

    var btn = li.querySelector('button.a-Menu-label');
    if (btn) {
      btn.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          toggleDarkMode();
        }
      });
    }

    return li;
  }

  /* ── 5. Inject into an open menu container ───────────────── */
  function injectIntoMenu(menu) {
    if (menu.querySelector('#' + INJECTED_ID)) return;   // already injected

    var ul = menu.querySelector('ul[role="group"]');
    if (!ul) return;

    /* Separator */
    var sep = document.createElement('li');
    sep.setAttribute('role', 'separator');
    sep.className = 'a-Menu-itemSep';
    sep.innerHTML = '<div class="a-Menu-inner">' +
                      '<span class="a-Menu-labelContainer">' +
                        '<span class="a-Menu-statusCol"></span>' +
                        '<span class="a-Menu-hSeparator"></span>' +
                      '</span>' +
                      '<span class="a-Menu-accelContainer"></span>' +
                    '</div>';

    ul.appendChild(sep);
    ul.appendChild(buildToggleItem());
    updateToggleVisual();
  }

  /* ── 6. Hook a user-menu button once we find it ──────────── */
  function hookMenuButton(btn) {
    var menuId = btn.getAttribute('data-menu');
    if (!menuId || hookedMenuIds[menuId]) return;
    hookedMenuIds[menuId] = true;

    /* Direct click hook — fires before the menu renders */
    btn.addEventListener('click', function () {
      /*
       * APEX v87 renders the menu div immediately on click and sets
       * display:block via inline style. A small delay lets the DOM
       * settle before we inject.
       */
      setTimeout(function () {
        var menu = document.getElementById(menuId);
        if (menu) injectIntoMenu(menu);
      }, 80);
    });

    /* If the menu is already open when we hook (e.g. re-navigation) */
    var existing = document.getElementById(menuId);
    if (existing && getComputedStyle(existing).display !== 'none') {
      injectIntoMenu(existing);
    }
  }

  /* ── 7. Scan the header for any [data-menu] nav buttons ──── */
  function scanForMenuButtons() {
    /*
     * APEX v87 nav bar user-menu button HTML (from live audit):
     *   <button id="L185585..." data-menu="menu_L185585..."
     *           class="t-Button t-Button--icon t-Button t-Button--header t-Button--navBar"
     *           aria-haspopup="menu">
     *
     * We match: [data-menu] inside the header nav bar.
     * We skip non-user-menu buttons (e.g. the "About" help button)
     * by preferring the button with .has-username on its parent LI,
     * then falling back to the last [data-menu] button in the header.
     */
    var allMenuBtns = Array.prototype.slice.call(
      document.querySelectorAll('.t-Header [data-menu], .t-NavigationBar [data-menu]')
    );

    if (!allMenuBtns.length) return false;

    /* Prefer the one whose parent LI has .has-username */
    var userBtn = null;
    for (var i = 0; i < allMenuBtns.length; i++) {
      var li = allMenuBtns[i].closest('li');
      if (li && li.classList.contains('has-username')) {
        userBtn = allMenuBtns[i];
        break;
      }
    }
    /* Fall back: last [data-menu] button in the header */
    if (!userBtn) userBtn = allMenuBtns[allMenuBtns.length - 1];

    hookMenuButton(userBtn);
    return true;
  }

  /* ── 8. Persistent MutationObserver — starts immediately ─── */
  function startObserver() {
    /*
     * KEY FIX FOR APEX v87:
     * The nav bar buttons are NOT present at DOMContentLoaded — APEX
     * injects them dynamically as part of the UT page hydration cycle.
     * We therefore cannot query for [data-menu] at init time. Instead,
     * we watch for childList mutations on the entire document and attempt
     * scanForMenuButtons() on every significant DOM change until we find
     * the button. Once found we disconnect the discovery observer and
     * rely only on the button's own click listener + the style observer.
     */
    var found = scanForMenuButtons();
    if (found) return; /* Already present — no observer needed */

    var discoveryObserver = new MutationObserver(function () {
      if (scanForMenuButtons()) {
        /* Found the button — stop the expensive childList scan */
        discoveryObserver.disconnect();

        /*
         * Now start a lightweight style-attribute observer that watches
         * for the menu div going display:block (belt-and-suspenders for
         * cases where the click listener fires before the div exists).
         */
        var allMenuBtns = Array.prototype.slice.call(
          document.querySelectorAll('.t-Header [data-menu]')
        );
        allMenuBtns.forEach(function (btn) {
          var menuId = btn.getAttribute('data-menu');
          if (!menuId) return;
          var menuDiv = document.getElementById(menuId);
          if (!menuDiv) return;

          styleObserver.observe(menuDiv, {
            attributes: true,
            attributeFilter: ['style'],
          });
        });
      }
    });

    discoveryObserver.observe(document.documentElement, {
      childList: true,
      subtree:   true,
    });

    /* Style observer — injected per menu div once we know its ID */
    var styleObserver = new MutationObserver(function (mutations) {
      mutations.forEach(function (m) {
        if (m.attributeName === 'style' &&
            m.target.style.display === 'block') {
          injectIntoMenu(m.target);
        }
      });
    });
  }

  /* ── 9. Initialise ───────────────────────────────────────── */
  function init() {
    applyPreference();
    startObserver();
    watchDialogIframes();
  }

  /* ── 10. Accessibility: inject ARIA labels on header chrome ─ */
  function patchA11y() {
    /*
     * APEX Universal Theme generates the nav bar header buttons without
     * accessible labels. The buttons contain only icon <span> elements
     * (FontApex icon font) and text <span> elements that are shown/hidden
     * at different breakpoints — but the text is not reliably exposed to
     * screen readers because it is hidden with CSS at narrow viewports.
     *
     * This function injects aria-label attributes on buttons/links that
     * are missing them. It runs once after the page is fully loaded.
     *
     * APEX v87 nav bar element map (from live diagnostic):
     *   #t_Button_navControl  — hamburger / side nav toggle
     *   .t-Header-logo-link   — app logo / home link
     *   Install App button    — PWA install prompt (a-pwaInstall)
     *   Feedback link         — opens feedback dialog
     *   About button          — help/info dropdown (#L1855851048950529356)
     *   User menu button      — account dropdown (#L1855852609035529354)
     *   .t-Footer-topButton   — back-to-top scroll button
     */
    function labelIfMissing(el, label) {
      if (!el) return;
      if (!el.getAttribute('aria-label') && !el.getAttribute('aria-labelledby')) {
        el.setAttribute('aria-label', label);
      }
    }

    /* Side-nav toggle */
    labelIfMissing(document.getElementById('t_Button_navControl'), 'Toggle navigation');

    /* App logo / home link */
    var logoLink = document.querySelector('.t-Header-logo-link');
    labelIfMissing(logoLink, 'Home');

    /* PWA Install App button */
    var installBtn = document.querySelector('.t-NavigationBar-item.a-pwaInstall a, .t-NavigationBar-item.a-pwaInstall button');
    labelIfMissing(installBtn, 'Install app');

    /* Feedback link — uses aria-roledescription already but still needs label */
    var feedbackBtn = document.querySelector('.t-NavigationBar-item a[href*="feedback"], .t-NavigationBar-item a[href*="Feedback"]');
    if (!feedbackBtn) {
      /* Fallback: find by icon class */
      feedbackBtn = document.querySelector('.t-NavigationBar-item a .fa-comment-o');
      if (feedbackBtn) feedbackBtn = feedbackBtn.closest('a');
    }
    labelIfMissing(feedbackBtn, 'Send feedback');

    /* About / help dropdown button — typically has .fa-question-circle-o */
    var aboutBtn = document.querySelector('.t-NavigationBar-item button .fa-question-circle-o');
    if (aboutBtn) labelIfMissing(aboutBtn.closest('button'), 'Help and about');

    /* User menu button — has .has-username on parent LI */
    var userLi = document.querySelector('.t-NavigationBar-item.has-username');
    if (userLi) {
      var userBtn = userLi.querySelector('button');
      if (userBtn) {
        var username = userBtn.querySelector('.t-Button-label');
        var labelText = username ? ('User menu: ' + username.textContent.trim()) : 'User menu';
        labelIfMissing(userBtn, labelText);
      }
    }

    /* Back-to-top button */
    var topBtn = document.querySelector('.t-Footer-topButton');
    labelIfMissing(topBtn, 'Back to top');

    /* Skip-to-content link — text is there but visually hidden via CSS clip;
       adding aria-label makes it unambiguous for all AT. */
    var skipLink = document.getElementById('t_Body_skipToContent');
    if (skipLink) {
      labelIfMissing(skipLink, 'Skip to main content');
    }

    /* Footer "Oracle APEX" link opens in a new window — label should say so */
    var apexFooterLink = document.querySelector('.t-Footer a[href*="apex.oracle"], .t-Footer a[href*="oracle"]');
    if (!apexFooterLink) {
      /* Fallback: find by text content */
      var footerLinks = Array.prototype.slice.call(document.querySelectorAll('.t-Footer a, footer a'));
      for (var fi = 0; fi < footerLinks.length; fi++) {
        if ((footerLinks[fi].textContent || '').toLowerCase().indexOf('apex') !== -1) {
          apexFooterLink = footerLinks[fi];
          break;
        }
      }
    }
    if (apexFooterLink && !apexFooterLink.getAttribute('aria-label')) {
      var existingText = apexFooterLink.textContent.trim();
      var opensNewWindow = apexFooterLink.target === '_blank' ||
                           (apexFooterLink.textContent || '').indexOf('new window') !== -1;
      apexFooterLink.setAttribute('aria-label',
        existingText + (opensNewWindow ? ' (opens in new window)' : ''));
    }
  }

  /*
   * Run as early as possible.
   * — If the script loads in <head> before DOMContentLoaded: wait for it.
   * — If it loads deferred / at bottom of <body>: run immediately.
   * — Also hook apex.jQuery ready as a belt-and-suspenders path for
   *   APEX apps that load JS files late in the page cycle.
   */
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () {
      init();
      patchA11y();
    });
  } else {
    init();
    patchA11y();
  }

  if (typeof apex !== 'undefined' && apex.jQuery) {
    apex.jQuery(document).ready(function () {
      applyPreference();
      startObserver();
      patchA11y();
    });
  } else {
    /* apex not yet defined — poll briefly so we catch the ready event */
    var apexPoll = setInterval(function () {
      if (typeof apex !== 'undefined' && apex.jQuery) {
        clearInterval(apexPoll);
        apex.jQuery(document).ready(function () {
          applyPreference();
          startObserver();
          patchA11y();
        });
      }
    }, 100);
    /* Give up after 10 seconds — DOMContentLoaded path is sufficient */
    setTimeout(function () { clearInterval(apexPoll); }, 10000);
  }

})();
