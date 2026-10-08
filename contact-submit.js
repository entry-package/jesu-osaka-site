(function () {
  'use strict';
  var form = document.querySelector('.native-form');
  if (!form) return;
  var button = form.querySelector('button[type="submit"]');
  var message = document.getElementById('contact-form-message');
  var requestId = document.getElementById('form-request-id');
  var pending = false;
  var timer;
  document.getElementById('form-open-ts').value = String(Date.now());

  function show(text) {
    message.hidden = false;
    message.textContent = text;
  }
  function finish(text) {
    clearTimeout(timer);
    pending = false;
    button.disabled = false;
    button.textContent = '送信する';
    show(text);
  }
  form.addEventListener('submit', function (event) {
    if (pending) { event.preventDefault(); return; }
    if (!window.crypto || !window.crypto.randomUUID) {
      event.preventDefault();
      show('安全な送信に対応した最新版のブラウザをご利用ください。');
      return;
    }
    requestId.value = window.crypto.randomUUID();
    pending = true;
    button.disabled = true;
    button.textContent = '送信結果を確認中…';
    show('送信結果を確認しています。この画面を閉じずにお待ちください。');
    timer = setTimeout(function () {
      // Keep pending=true so a late genuine success can still be acknowledged.
      // Do not invite an immediate resend after an ambiguous network outcome.
      show('送信結果を確認できていません。受付メールをご確認ください。届かない場合は、入力内容を控えたうえで公式Xなど別の窓口からお問い合わせください。重複送信を防ぐため、再送信はお控えください。');
    }, 45000);
  });
  window.addEventListener('message', function (event) {
    // Apps Script nests its response inside a googleusercontent sandbox iframe.
    // Exact Google-origin allowlist plus a per-request cryptographic nonce.
    if (!/^https:\/\/(?:script\.google\.com|script\.googleusercontent\.com|[a-z0-9-]+-script\.googleusercontent\.com)$/.test(event.origin)) return;
    var data = event.data;
    if (!pending || !data || data.type !== 'jesu-contact-result' || data.requestId !== requestId.value) return;
    if (data.status === 'sent' || data.status === 'duplicate') {
      clearTimeout(timer);
      pending = false;
      window.location.href = './contact-thanks.html';
    } else if (data.status === 'uncertain') {
      clearTimeout(timer);
      show('受付処理の結果を確認できません。受付メールをご確認ください。届かない場合は公式Xなど別の窓口からお問い合わせください。重複送信を防ぐため、再送信はお控えください。');
    } else if (data.status === 'ratelimit') {
      finish('送信回数の上限に達したため、今回は受付できませんでした。10分以上あけてお試しください。繰り返し表示される場合は翌日以降にお試しいただくか、公式Xなど別の窓口をご利用ください。');
    } else if (['invalid', 'blocked', 'busy', 'unavailable'].indexOf(data.status) >= 0) {
      finish('受付を完了できませんでした。入力内容を確認し、時間をおいてお試しください。繰り返し表示される場合は公式Xなど別の窓口をご利用ください。');
    }
  });
})();
