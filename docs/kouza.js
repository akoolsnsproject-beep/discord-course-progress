/* NEXORA講座：チェック＋クリアボタン（LIFF） */
(function () {
  var LIFF_ID = '2012700328-ixoZeXYW';
  var OA = '@982rpclz';
  var m = location.pathname.match(/step(\d)-(win|mac)\.html/);
  if (!m) return;
  var n = +m[1], os = m[2], osName = os === 'win' ? 'Windows' : 'Mac';
  var MSG = '✅ STEP' + n + 'クリア' + (os === 'mac' ? '！' : '');
  var KEY = 'nx_s' + n + os;

  var css = document.createElement('style');
  css.textContent =
    '.ck{display:flex;align-items:center;justify-content:center;gap:10px;margin:12px 0 4px;padding:13px;border-radius:14px;border:2px dashed #ff8a24;color:#ffb066;font-weight:900;font-size:16px;background:rgba(255,138,36,.06);cursor:pointer;user-select:none;-webkit-tap-highlight-color:transparent}' +
    '.ck i{width:24px;height:24px;border-radius:7px;border:2.5px solid #ff8a24;display:inline-block;font-style:normal;line-height:20px;text-align:center}' +
    '.ck.on{border-style:solid;background:#ff7a12;color:#fff;border-color:#ff7a12;box-shadow:0 0 18px rgba(255,122,18,.55)}' +
    '.ck.on i{background:#fff;border-color:#fff;color:#ff6a00}' +
    '.fin{margin:26px 0 30px;padding:20px 16px;border-radius:20px;text-align:center;border:2px solid #333;background:#111}' +
    '.fin .t{font-size:15px;color:#aaa;font-weight:700;margin-bottom:12px}' +
    '.fin .b{display:block;width:100%;border:0;padding:18px;border-radius:16px;font-size:19px;font-weight:900;background:#333;color:#777;font-family:inherit}' +
    '.fin.on{border-color:#ff8a24;box-shadow:0 0 30px rgba(255,138,36,.45);background:linear-gradient(180deg,#1d0f05,#0b0705)}' +
    '.fin.on .t{color:#ffcf99}' +
    '.fin.on .b{background:linear-gradient(135deg,#ffb04a,#ff5a00);color:#fff;box-shadow:0 0 24px rgba(255,106,0,.7);cursor:pointer}' +
    '.fin .s{margin-top:10px;font-size:13px;color:#ffb066;min-height:1em}';
  document.head.appendChild(css);

  var saved = [];
  try { saved = JSON.parse(localStorage.getItem(KEY) || '[]'); } catch (e) {}

  var secs = [].slice.call(document.querySelectorAll('.sec'));
  var total = secs.length;
  var fin = document.createElement('div');
  fin.className = 'fin';
  var goal = document.querySelector('.goal');
  if (goal) goal.replaceWith(fin); else secs[total - 1].after(fin);

  function done() { return secs.filter(function (s) { return s.classList.contains('done'); }).length; }
  function save() {
    var a = secs.map(function (s) { return s.classList.contains('done') ? 1 : 0; });
    try { localStorage.setItem(KEY, JSON.stringify(a)); } catch (e) {}
  }
  function render() {
    var d = done(), all = d >= total;
    var pc = document.getElementById('pc2'); if (pc) pc.textContent = '✓ ' + d + ' / ' + total;
    var pb = document.getElementById('pb2'); if (pb) pb.style.width = (d / total * 100) + '%';
    fin.className = 'fin' + (all ? ' on' : '');
    fin.innerHTML = all
      ? '<div class="t">🎉 ぜんぶチェックできました！</div><button class="b" id="clr">STEP' + n + ' クリア！ LINEに送る ▶</button><div class="s" id="st"></div>'
      : '<div class="t">ぜんぶチェックすると、ここにボタンが出ます（あと' + (total - d) + 'つ）</div><span class="b">🔒 STEP' + n + ' クリア</span>';
    if (all) document.getElementById('clr').onclick = send;
  }
  secs.forEach(function (s, i) {
    var c = document.createElement('div');
    c.className = 'ck';
    function paint() {
      var on = s.classList.contains('done');
      c.classList.toggle('on', on);
      c.innerHTML = on ? '<i>✓</i>できた！' : '<i></i>ここまでできたらタップ';
    }
    if (saved[i]) s.classList.add('done');
    paint();
    c.onclick = function () { s.classList.toggle('done'); paint(); save(); render(); };
    s.appendChild(c);
  });
  // スクロールで数字を書きかえる元の処理を、見えないダミーに向ける
  ['pc', 'pb'].forEach(function (id) {
    var e = document.getElementById(id); if (!e) return;
    e.id = id + '2';
    var d = document.createElement('i'); d.id = id; d.style.display = 'none'; document.body.appendChild(d);
  });
  render();

  var ready = false;
  function send() {
    var st = document.getElementById('st'), b = document.getElementById('clr');
    if (window.liff && ready && liff.isInClient()) {
      b.disabled = true; st.textContent = '送っています…';
      liff.sendMessages([{ type: 'text', text: MSG }]).then(function () {
        st.textContent = '送りました！LINEにもどります';
        setTimeout(function () { liff.closeWindow(); }, 600);
      }).catch(function () {
        b.disabled = false; fallback();
      });
    } else { fallback(); }
  }
  function fallback() {
    location.href = 'https://line.me/R/oaMessage/' + encodeURIComponent(OA) + '/?' + encodeURIComponent(MSG);
  }

  var sdk = document.createElement('script');
  sdk.src = 'https://static.line-scdn.net/liff/edge/2/sdk.js';
  sdk.onload = function () {
    liff.init({ liffId: LIFF_ID }).then(function () { ready = true; }).catch(function () {});
  };
  document.head.appendChild(sdk);
})();
