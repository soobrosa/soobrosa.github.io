/* Paper <-> inverted polarity toggle. Press T to switch. */
(function () {
  var KEY = 'soob-theme';
  var root = document.documentElement;
  function apply(t) {
    if (t === 'invert') root.setAttribute('data-theme', 'invert');
    else root.removeAttribute('data-theme');
  }
  var saved;
  try { saved = localStorage.getItem(KEY); } catch (e) {}
  apply(saved === 'invert' ? 'invert' : 'paper');
  document.addEventListener('keydown', function (e) {
    if (e.key !== 't' && e.key !== 'T') return;
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    var el = document.activeElement;
    if (el && /^(input|textarea|select)$/i.test(el.tagName)) return;
    var next = root.getAttribute('data-theme') === 'invert' ? 'paper' : 'invert';
    apply(next);
    try { localStorage.setItem(KEY, next); } catch (e) {}
  });
})();
