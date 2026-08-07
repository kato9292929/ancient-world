// スクロール連動の上乗せ。重いライブラリは持ち込まない。IntersectionObserver と DOM のみ。
// JS 無効ならこのファイルは読まれず、静的な一覧がそのまま残る。
(function () {
  "use strict";

  var readoutYear = document.querySelector(".readout-year");
  var events = Array.prototype.slice.call(document.querySelectorAll(".event"));
  if (events.length === 0) return;

  var reduce =
    window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // 左の年代表示をスクロールに連動させる。ビューポート中央を横切った出来事の年代を出す。
  if (readoutYear && "IntersectionObserver" in window) {
    var current = null;
    var yearObserver = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) current = entry.target;
        });
        if (current) {
          var y = current.getAttribute("data-year");
          if (y) readoutYear.textContent = y;
        }
      },
      { rootMargin: "-50% 0px -50% 0px", threshold: 0 },
    );
    events.forEach(function (el) {
      yearObserver.observe(el);
    });
  }

  // 入場アニメーション。動きを減らす設定なら付けない（全項目は最初から見えている）。
  if (!reduce && "IntersectionObserver" in window) {
    var revealObserver = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("in-view");
            revealObserver.unobserve(entry.target);
          }
        });
      },
      { rootMargin: "0px 0px -10% 0px", threshold: 0.1 },
    );
    events.forEach(function (el) {
      revealObserver.observe(el);
    });
  } else {
    events.forEach(function (el) {
      el.classList.add("in-view");
    });
  }
})();
