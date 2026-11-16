/* Блок LISTEN с прокруткой: видны первые строки площадок, остальные листаются внутри блока.
   Кнопка под блоком опускает список вниз и возвращает наверх. Без скриптов видны все площадки. */
(function () {
  'use strict';
  var box = document.querySelector('[data-scroller]');
  if (!box) return;
  var view = box.querySelector('[data-scroller-view]');
  var more = box.querySelector('[data-scroller-more]');
  if (!view || !more) return;

  box.classList.add('is-on');
  more.hidden = false;

  function update() {
    var max = view.scrollHeight - view.clientHeight;
    box.classList.toggle('is-end', max <= 2 || view.scrollTop >= max - 2);
    box.classList.toggle('is-top', view.scrollTop <= 2);
    more.hidden = max <= 2;
  }
  var ticking = false;
  view.addEventListener('scroll', function () {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(function () { ticking = false; update(); });
  }, { passive: true });
  window.addEventListener('resize', update);

  more.addEventListener('click', function () {
    var end = box.classList.contains('is-end');
    var top = end ? 0 : view.scrollHeight - view.clientHeight;
    var calm = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    try { view.scrollTo({ top: top, behavior: calm ? 'auto' : 'smooth' }); }
    catch (e) { view.scrollTop = top; }
  });
  update();
})();
