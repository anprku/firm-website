/* Earlier / later links at the foot of each article, built from the archive list
   so that a new article only needs to be added to articles/index.html. */

(function () {
  var main = document.querySelector('main.article-body');
  if (!main || !window.fetch || !window.DOMParser) return;

  var here = location.pathname.split('/').pop() || '';

  fetch('/articles/index.html')
    .then(function (r) { return r.ok ? r.text() : Promise.reject(); })
    .then(function (text) {
      var doc = new DOMParser().parseFromString(text, 'text/html');
      var links = Array.prototype.slice.call(doc.querySelectorAll('.archive-list ul li a'));
      var i = links.findIndex(function (a) {
        return a.getAttribute('href').split('/').pop() === here;
      });
      if (i < 0) return;

      // The archive lists newest first.
      var later = links[i - 1];
      var earlier = links[i + 1];
      if (!later && !earlier) return;

      var nav = document.createElement('nav');
      nav.className = 'article-nav';
      nav.setAttribute('aria-label', 'More notes');

      function item(a, label, cls) {
        var el = document.createElement(a ? 'a' : 'span');
        el.className = cls;
        if (a) {
          el.href = '/articles/' + a.getAttribute('href').split('/').pop();
          var small = document.createElement('span');
          small.className = 'article-nav-label';
          small.textContent = label;
          var title = document.createElement('span');
          title.className = 'article-nav-title';
          title.textContent = a.querySelector('.art-title').textContent.trim();
          el.appendChild(small);
          el.appendChild(title);
        }
        return el;
      }

      nav.appendChild(item(earlier, '← Earlier', 'article-nav-earlier'));
      nav.appendChild(item(later, 'Later →', 'article-nav-later'));
      main.appendChild(nav);
    })
    .catch(function () {});
})();
