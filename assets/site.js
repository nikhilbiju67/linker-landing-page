/* Linkker site — small, dependency-free progressive enhancement. */
(function () {
  'use strict';

  var doc = document.documentElement;
  var reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---------- Header: mobile nav + scrolled state ---------- */
  var toggle = document.querySelector('.nav-toggle');
  var nav = document.getElementById('site-nav');
  if (toggle && nav) {
    var closeNav = function () {
      toggle.setAttribute('aria-expanded', 'false');
      toggle.setAttribute('aria-label', 'Open menu');
      nav.classList.remove('is-open');
    };
    toggle.addEventListener('click', function () {
      var open = toggle.getAttribute('aria-expanded') === 'true';
      toggle.setAttribute('aria-expanded', String(!open));
      toggle.setAttribute('aria-label', open ? 'Open menu' : 'Close menu');
      nav.classList.toggle('is-open', !open);
      if (!open) { var first = nav.querySelector('a'); if (first) first.focus(); }
    });
    nav.addEventListener('click', function (e) { if (e.target.closest('a')) closeNav(); });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && nav.classList.contains('is-open')) { closeNav(); toggle.focus(); }
    });
    window.addEventListener('resize', function () { if (window.innerWidth > 860) closeNav(); });
  }
  var header = document.querySelector('.site-header');
  if (header) {
    var onScroll = function () { header.classList.toggle('is-scrolled', window.scrollY > 8); };
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
  }

  /* ---------- Footer year ---------- */
  var years = document.querySelectorAll('[data-year]');
  for (var y = 0; y < years.length; y++) years[y].textContent = String(new Date().getFullYear());

  /* ---------- Reveal + play illustrations when visible ---------- */
  var revealEls = document.querySelectorAll('.reveal');
  var illos = document.querySelectorAll('[data-illo]');
  if ('IntersectionObserver' in window) {
    var revealIO = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) { entry.target.classList.add('is-visible'); revealIO.unobserve(entry.target); }
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
    revealEls.forEach(function (el) { revealIO.observe(el); });

    // Illustrations animate only while on screen (saves battery, keeps it calm)
    var illoIO = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        var el = entry.target;
        if (reduceMotion) return;
        el.classList.toggle('play', entry.isIntersecting);
        if (entry.isIntersecting && el.dataset.illo === 'copy' && !el.dataset.demoed) {
          el.dataset.demoed = '1';
          setTimeout(function () { runCopy(el.querySelector('.copy-btn'), false); }, 900);
        }
        if (entry.isIntersecting && el.dataset.illo === 'lock' && !el.dataset.demoed) {
          el.dataset.demoed = '1';
          setTimeout(function () { if (!el.dataset.user) runUnlock(el, true); }, 1100);
        }
      });
    }, { threshold: 0.35 });
    illos.forEach(function (el) { illoIO.observe(el); });
  } else {
    revealEls.forEach(function (el) { el.classList.add('is-visible'); });
  }

  /* ---------- Hero logo: intro once, loop on hover/click ---------- */
  var heroArt = document.querySelector('.hero-art');
  var heroLogo = document.querySelector('.hero-art .lk');
  if (heroArt && heroLogo) {
    if (reduceMotion) {
      heroArt.classList.add('is-ready');
    } else {
      heroLogo.classList.add('intro');
      setTimeout(function () { heroArt.classList.add('is-ready'); }, 250);
    }
    var replay = heroArt.querySelector('.hero-tile button');
    if (replay) {
      replay.addEventListener('click', function () {
        if (reduceMotion) return;
        heroLogo.classList.remove('intro', 'loop');
        void heroLogo.getBoundingClientRect();
        heroLogo.classList.add('intro');
      });
      replay.addEventListener('mouseenter', function () { if (!reduceMotion) { heroLogo.classList.remove('intro'); heroLogo.classList.add('loop'); } });
      replay.addEventListener('mouseleave', function () { heroLogo.classList.remove('loop'); });
    }
  }

  /* ---------- One-tap copy demo ---------- */
  function runCopy(btn, reallyCopy) {
    if (!btn || btn.classList.contains('is-done')) return;
    var text = btn.getAttribute('data-copy') || '';
    if (reallyCopy && navigator.clipboard && text) {
      navigator.clipboard.writeText(text).catch(function () {});
    }
    btn.classList.add('is-done');
    var live = document.getElementById('copy-live');
    if (live && reallyCopy) live.textContent = 'Link copied to clipboard';
    setTimeout(function () { btn.classList.remove('is-done'); if (live) live.textContent = ''; }, 2200);
  }
  document.querySelectorAll('.copy-btn').forEach(function (btn) {
    btn.addEventListener('click', function () { runCopy(btn, true); });
  });

  /* ---------- Not-safe-for-work unlock demo ---------- */
  function runUnlock(illo, auto) {
    if (!illo || illo.dataset.busy) return;
    var dots = illo.querySelectorAll('.pin .dots span');
    var btn = illo.querySelector('.unlock-btn');
    var status = illo.querySelector('.lock-status');
    if (illo.classList.contains('is-unlocked')) {
      illo.classList.remove('is-unlocked');
      dots.forEach(function (d) { d.classList.remove('on'); });
      if (btn) { btn.querySelector('.lbl').textContent = 'Unlock'; btn.setAttribute('aria-pressed', 'false'); }
      if (status) status.textContent = 'Hidden links locked';
      return;
    }
    illo.dataset.busy = '1';
    var i = 0;
    var step = reduceMotion ? 0 : 180;
    (function fill() {
      if (i < dots.length) { dots[i].classList.add('on'); i++; setTimeout(fill, step); return; }
      illo.classList.add('is-unlocked');
      if (btn) { btn.querySelector('.lbl').textContent = 'Lock'; btn.setAttribute('aria-pressed', 'true'); }
      if (status) status.textContent = 'Hidden links unlocked';
      delete illo.dataset.busy;
      if (auto) setTimeout(function () { if (!illo.dataset.user) runUnlock(illo, false); }, 2600);
    })();
  }
  document.querySelectorAll('[data-illo="lock"] .unlock-btn').forEach(function (btn) {
    btn.addEventListener('click', function () { var il = btn.closest('[data-illo]'); il.dataset.user = '1'; runUnlock(il, false); });
  });

  /* ---------- Promo video: lazy, muted autoplay loop while visible ---------- */
  var video = document.querySelector('[data-promo]');
  if (video) {
    var playBtn = document.querySelector('[data-video-play]');
    var muteBtn = document.querySelector('[data-video-mute]');
    var loaded = false;
    var userPaused = false;
    var load = function () {
      if (loaded) return;
      loaded = true;
      var src = video.getAttribute('data-src');
      if (src) { video.src = src; video.load(); }
    };
    var setPlayState = function () {
      if (!playBtn) return;
      var playing = !video.paused;
      playBtn.setAttribute('data-state', playing ? 'b' : 'a');
      playBtn.setAttribute('aria-label', playing ? 'Pause video' : 'Play video');
    };
    var setMuteState = function () {
      if (!muteBtn) return;
      muteBtn.setAttribute('data-state', video.muted ? 'a' : 'b');
      muteBtn.setAttribute('aria-label', video.muted ? 'Unmute video' : 'Mute video');
    };
    video.addEventListener('play', setPlayState);
    video.addEventListener('pause', setPlayState);
    video.addEventListener('volumechange', setMuteState);
    if (playBtn) playBtn.addEventListener('click', function () {
      load();
      if (video.paused) { userPaused = false; video.play().catch(function () {}); }
      else { userPaused = true; video.pause(); }
    });
    if (muteBtn) muteBtn.addEventListener('click', function () {
      load();
      video.muted = !video.muted;
      if (!video.muted && video.paused) video.play().catch(function () {});
    });
    if (!reduceMotion && 'IntersectionObserver' in window) {
      new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            load();
            if (!userPaused) video.play().catch(function () {});
          } else if (!video.paused) {
            video.pause();
          }
        });
      }, { threshold: 0.4 }).observe(video);
    }
    setPlayState();
    setMuteState();
  }

  /* ---------- Account deletion request (mailto, no backend) ---------- */
  var delForm = document.getElementById('deletion-form');
  if (delForm) {
    var msg = document.getElementById('deletion-msg');
    var show = function (text, ok) {
      msg.textContent = text;
      msg.className = 'form-msg ' + (ok ? 'is-ok' : 'is-error');
      msg.focus();
    };
    delForm.addEventListener('submit', function (e) {
      e.preventDefault();
      var email = delForm.elements.email.value.trim();
      var confirmEmail = delForm.elements.confirm.value.trim();
      var scope = delForm.elements.scope.value;
      var platform = delForm.elements.platform.value;
      var note = delForm.elements.note.value.trim();
      var understand = delForm.elements.understand.checked;
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) { show('Please enter the email address you use to sign in to Linkker.', false); delForm.elements.email.focus(); return; }
      if (email.toLowerCase() !== confirmEmail.toLowerCase()) { show('The two email addresses do not match.', false); delForm.elements.confirm.focus(); return; }
      if (!understand) { show('Please confirm you understand that deletion is permanent.', false); delForm.elements.understand.focus(); return; }
      var to = delForm.getAttribute('data-to');
      var subject = 'Linkker account deletion request';
      var body = [
        'Hello Linkker team,',
        '',
        'Please delete my Linkker account and the associated data.',
        '',
        'Account email: ' + email,
        'Request: ' + scope,
        'I signed in with / use Linkker on: ' + platform,
        note ? 'Notes: ' + note : '',
        '',
        'I understand that deletion is permanent and cannot be undone.',
        '',
        'Sent from the account deletion page (' + location.origin + '/delete-account) on ' + new Date().toISOString().slice(0, 10) + '.'
      ].filter(function (l, idx, arr) { return !(l === '' && arr[idx - 1] === ''); }).join('\n');
      var href = 'mailto:' + to + '?subject=' + encodeURIComponent(subject) + '&body=' + encodeURIComponent(body);
      delForm.setAttribute('data-last-mailto', href);
      window.location.href = href;
      show('Your email app should open with the request filled in — just press Send. If nothing opened, email ' + to + ' from the address on your account with the subject "' + subject + '".', true);
    });
  }

  /* ---------- Checkout return page: reflect Dodo/RevenueCat status param ---------- */
  var checkout = document.querySelector('[data-checkout]');
  if (checkout) {
    var params = new URLSearchParams(location.search);
    var status = (params.get('status') || '').toLowerCase();
    if (status && ['failed', 'cancelled', 'canceled', 'expired'].indexOf(status) !== -1) {
      checkout.setAttribute('data-state', 'failed');
      document.title = 'Payment not completed · Linkker';
    }
  }
})();
