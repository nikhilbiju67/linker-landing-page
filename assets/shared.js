/* Shared-collection page: fetches the public read-only collection and renders it with textContent only. */
(function () {
  'use strict';

  var PROD_API = 'https://1v71w41bn5.execute-api.ap-south-1.amazonaws.com/prod';
  var PAGE = 24;
  var SVG_NS = 'http://www.w3.org/2000/svg';
  var isLocal = /^(localhost|127\.0\.0\.1|\[::1\])$/.test(location.hostname);
  var API = isLocal ? location.origin + '/mockapi' : PROD_API;

  var $ = function (id) { return document.getElementById(id); };
  var els = {
    name: $('sc-title'), desc: $('sc-desc'), meta: $('sc-meta'),
    status: $('sc-status'), list: $('sc-list'), more: $('sc-more')
  };

  var token = (function () {
    var m = location.pathname.match(/^\/c\/([^/?#]+)/);
    var t = m ? m[1] : (isLocal ? new URLSearchParams(location.search).get('t') : null);
    try { t = t && decodeURIComponent(t); } catch (e) { return null; }
    return t && /^[A-Za-z0-9_-]{3,128}$/.test(t) ? t : null;
  })();

  var offset = 0, total = 0, loading = false, shown = 0;

  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }

  function icon(id) {
    var s = document.createElementNS(SVG_NS, 'svg');
    s.setAttribute('aria-hidden', 'true');
    var u = document.createElementNS(SVG_NS, 'use');
    u.setAttribute('href', '/assets/icons.svg#' + id);
    s.appendChild(u);
    return s;
  }

  function safeUrl(raw) {
    if (typeof raw !== 'string') return null;
    try {
      var u = new URL(raw.trim());
      return u.protocol === 'https:' || u.protocol === 'http:' ? u : null;
    } catch (e) { return null; }
  }

  function str(v, max) {
    if (typeof v !== 'string') return '';
    v = v.replace(/\s+/g, ' ').trim();
    return v.length > max ? v.slice(0, max) : v;
  }

  function clearStatus() { els.status.textContent = ''; }

  function showState(title, body, actionLabel, action) {
    clearStatus();
    var box = el('div', 'sc-state card');
    box.appendChild(el('h2', null, title));
    box.appendChild(el('p', null, body));
    if (actionLabel) {
      var b = el('button', 'btn btn--primary', actionLabel);
      b.type = 'button';
      b.addEventListener('click', action);
      box.appendChild(b);
    } else {
      var a = el('a', 'btn btn--primary', 'Get Linkker');
      a.href = '/#download';
      box.appendChild(a);
    }
    els.status.appendChild(box);
  }

  function skeletons(n) {
    for (var i = 0; i < n; i++) {
      var li = el('li', 'sc-item sc-skel');
      li.setAttribute('data-skel', '1');
      var card = el('div', 'sc-link');
      card.appendChild(el('div', 'sc-thumb'));
      var body = el('div', 'sc-body');
      body.appendChild(el('div', 'sc-line'));
      body.appendChild(el('div', 'sc-line w60'));
      card.appendChild(body);
      li.appendChild(card);
      els.list.appendChild(li);
    }
  }

  function removeSkeletons() {
    var s = els.list.querySelectorAll('[data-skel]');
    for (var i = 0; i < s.length; i++) s[i].remove();
  }

  function thumb(link) {
    var box = el('div', 'sc-thumb');
    var src = safeUrl(link.thumbnail);
    if (!src) {
      box.className += ' sc-thumb--empty';
      box.appendChild(icon('i-link'));
      return box;
    }
    var img = document.createElement('img');
    img.alt = '';
    img.loading = 'lazy';
    img.decoding = 'async';
    img.referrerPolicy = 'no-referrer';
    img.addEventListener('error', function () {
      box.textContent = '';
      box.className = 'sc-thumb sc-thumb--empty';
      box.appendChild(icon('i-link'));
    });
    img.src = src.href;
    box.appendChild(img);
    return box;
  }

  function card(link) {
    var li = el('li', 'sc-item');
    var u = safeUrl(link && link.url);
    if (!u) return null;
    var a = el('a', 'sc-link');
    a.href = u.href;
    a.target = '_blank';
    a.rel = 'noopener noreferrer nofollow ugc';
    a.appendChild(thumb(link));
    var body = el('div', 'sc-body');
    var host = u.hostname.replace(/^www\./, '');
    body.appendChild(el('div', 'sc-title', str(link.title, 200) || host));
    var d = str(link.description, 300);
    if (d) body.appendChild(el('div', 'sc-blurb', d));
    body.appendChild(el('div', 'sc-host', host));
    a.appendChild(body);
    li.appendChild(a);
    return li;
  }

  function renderHead(c, count) {
    var name = str(c && c.name, 120) || 'Shared collection';
    els.name.textContent = name;
    document.title = name + ' · Linkker';
    var d = str(c && c.description, 400);
    els.desc.hidden = !d;
    els.desc.textContent = d;
    var n = typeof count === 'number' ? count : 0;
    els.meta.hidden = false;
    els.meta.textContent = n + (n === 1 ? ' link' : ' links');
  }

  function fetchPage() {
    var ctl = typeof AbortController === 'function' ? new AbortController() : null;
    var timer = setTimeout(function () { if (ctl) ctl.abort(); }, 15000);
    var url = API + '/social/collections/' + encodeURIComponent(token) + '?limit=' + PAGE + '&offset=' + offset;
    return fetch(url, {
      method: 'GET', headers: { Accept: 'application/json' },
      credentials: 'omit', referrerPolicy: 'no-referrer', cache: 'no-store',
      signal: ctl ? ctl.signal : undefined
    }).then(function (res) {
      clearTimeout(timer);
      if (res.status === 404) { var e = new Error('gone'); e.gone = true; throw e; }
      if (!res.ok) throw new Error('http ' + res.status);
      return res.json();
    }, function (err) { clearTimeout(timer); throw err; });
  }

  function load() {
    if (loading) return;
    loading = true;
    els.more.hidden = true;
    clearStatus();
    skeletons(offset === 0 ? 6 : 3);
    fetchPage().then(function (json) {
      removeSkeletons();
      var data = (json && json.data) || {};
      var links = Array.isArray(data.links) ? data.links : [];
      total = typeof data.total === 'number' ? data.total : offset + links.length;
      if (offset === 0) renderHead(data.collection, total);
      for (var i = 0; i < links.length; i++) {
        var c = card(links[i]);
        if (c) { els.list.appendChild(c); shown++; }
      }
      offset += links.length;
      if (shown === 0 && offset >= total) {
        showState('Nothing to show yet', 'This collection has no links you can view right now.');
      }
      els.more.hidden = !(links.length > 0 && offset < total);
    }).catch(function (err) {
      removeSkeletons();
      if (err && err.gone) {
        els.name.textContent = 'This link has stopped working';
        document.title = 'Collection unavailable · Linkker';
        els.meta.hidden = true;
        showState('This collection is no longer shared', 'The owner may have stopped sharing it, or the link was typed wrong. Ask them for a fresh link.');
      } else {
        showState('Could not load this collection', 'Check your connection and try again.', 'Try again', function () { loading = false; load(); });
      }
    }).then(function () { loading = false; });
  }

  els.more.addEventListener('click', load);

  if (!token) {
    els.name.textContent = 'This link has stopped working';
    els.meta.hidden = true;
    showState('This collection is no longer shared', 'The link looks incomplete. Ask the owner to send it again.');
  } else {
    load();
  }
})();
