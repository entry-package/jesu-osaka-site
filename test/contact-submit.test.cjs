const { test } = require('node:test');
const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const vm = require('node:vm');
const source = readFileSync(new URL('../contact-submit.js', `file://${__filename}`), 'utf8');
function setup() {
  const listeners = {}; const button = { disabled: false }; const message = { hidden: true };
  const fields = { 'contact-form-message': message, 'form-request-id': {}, 'form-open-ts': {} };
  const form = { querySelector: () => button, addEventListener: (type, fn) => listeners[type] = fn };
  const window = { crypto: { randomUUID: () => '11111111-2222-4333-8444-555555555555' }, location: { href: 'form' }, addEventListener: (type, fn) => listeners[type] = fn };
  let timer; let prevented = false;
  vm.runInNewContext(source, { window, document: { querySelector: () => form, getElementById: id => fields[id] }, setTimeout: fn => { timer = fn; return 1; }, clearTimeout: () => {} });
  return { window, button, message, submit() { prevented = false; listeners.submit({ preventDefault: () => { prevented = true; } }); return prevented; }, timeout() { timer(); }, response(status, origin='https://abc-script.googleusercontent.com', nonce=fields['form-request-id'].value) { listeners.message({ origin, data: { type: 'jesu-contact-result', requestId: nonce, status } }); } };
}
test('submission waits for a checked response; duplicate clicks cannot submit', () => { const h=setup(); assert.equal(h.submit(),false); assert.equal(h.button.disabled,true); assert.equal(h.window.location.href,'form'); assert.equal(h.submit(),true); });
for (const status of ['sent','duplicate']) test(status+' navigates to completion',()=>{const h=setup();h.submit();h.response(status);assert.equal(h.window.location.href,'./contact-thanks.html');});
test('wrong origin and wrong nonce never acknowledge submission',()=>{const h=setup();h.submit();h.response('sent','https://script.googleusercontent.com.evil.test');h.response('sent','https://script.googleusercontent.com','wrong');assert.equal(h.window.location.href,'form');});
for (const status of ['invalid','blocked','busy','ratelimit','unavailable']) test(status+' stays on form and shows failure',()=>{const h=setup();h.submit();h.response(status);assert.equal(h.window.location.href,'form');assert.equal(h.button.disabled,false);assert.equal(h.message.hidden,false);});
test('uncertain outcome prevents a blind resend',()=>{const h=setup();h.submit();h.response('uncertain');assert.equal(h.window.location.href,'form');assert.equal(h.submit(),true);});
test('timeout never claims success but accepts a late genuine response',()=>{const h=setup();h.submit();h.timeout();assert.equal(h.window.location.href,'form');assert.match(h.message.textContent,/確認できていません/);h.response('sent');assert.equal(h.window.location.href,'./contact-thanks.html');});
test('missing secure random support prevents submission',()=>{const h=setup();h.window.crypto=null;assert.equal(h.submit(),true);assert.equal(h.button.disabled,false);});
test('markup no longer treats iframe load as successful acceptance',()=>{const html=readFileSync(new URL('../contact.html',`file://${__filename}`),'utf8');assert.doesNotMatch(html,/onload=|contactFormSubmitted/);assert.match(html,/contact-submit.js/);assert.match(html,/maxlength="4000"/);});
