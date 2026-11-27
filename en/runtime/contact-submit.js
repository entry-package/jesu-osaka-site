(function () {
  'use strict';
  var form = document.querySelector('.native-form');
  if (!form) return;
  if (form.hasAttribute('data-preview-form')) {
    form.addEventListener('submit', function (event) { event.preventDefault(); });
    return;
  }
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
    button.textContent = 'Send inquiry';
    show(text);
  }
  form.addEventListener('submit', function (event) {
    if (pending) { event.preventDefault(); return; }
    if (!window.crypto || !window.crypto.randomUUID) {
      event.preventDefault();
      show('Use a current browser that supports secure submission.');
      return;
    }
    requestId.value = window.crypto.randomUUID();
    pending = true;
    button.disabled = true;
    button.textContent = 'Checking your submission…';
    show('Please keep this page open while we check your submission.');
    timer = setTimeout(function () {
      // Keep pending=true so a late genuine success can still be acknowledged.
      // Do not invite an immediate resend after an ambiguous network outcome.
      show('We could not confirm your submission. Check for a confirmation email. If none arrives, save your message and contact us through another channel, such as our official X account. Avoid resubmitting to prevent duplicates.');
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
      window.location.href = form.dataset.successUrl;
    } else if (data.status === 'uncertain') {
      clearTimeout(timer);
      show('We could not confirm receipt. Check for a confirmation email. If none arrives, contact us through another channel, such as our official X account. Avoid resubmitting to prevent duplicates.');
    } else if (data.status === 'ratelimit') {
      finish('You have reached the submission limit. Wait at least ten minutes and try again. If the message persists, try the next day or use another channel, such as our official X account.');
    } else if (['invalid', 'blocked', 'busy', 'unavailable'].indexOf(data.status) >= 0) {
      finish('We could not complete your submission. Check your details and try again later. If the issue persists, use another channel, such as our official X account.');
    }
  });
})();
