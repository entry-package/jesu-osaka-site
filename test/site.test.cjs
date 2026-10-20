const {test}=require('node:test');
const assert=require('node:assert/strict');
const vm=require('node:vm');
const {readFileSync}=require('node:fs');
const source=readFileSync(new URL('../site.js',`file://${__filename}`),'utf8');
function run({host='www.jesu-osaka.jp',date='2026-10-20T00:00:00Z',withForm=true}={}){
 const button={disabled:false,textContent:'送信する'}, status={},link={},heading={textContent:'開催予定'};
 const listeners={};const form={querySelector:()=>button,addEventListener:(type,fn)=>listeners[type]=fn};
 const card={dataset:{eventEnd:'2026-10-26T22:00:00+09:00'},querySelector:q=>q==='[data-event-status]'?status:link};
 const document={querySelector:q=>q==='.native-form'?(withForm?form:null):q==='#upcoming h2'?heading:null,querySelectorAll:()=>[card]};
 vm.runInNewContext(source,{document,location:{hostname:host},Date:{now:()=>Date.parse(date),parse:Date.parse}});
 return {button,status,link,heading,listeners};
}
for(const host of ['www.jesu-osaka.jp','jesu-osaka.jp'])test('production retains submission on '+host,()=>assert.equal(run({host}).button.disabled,false));
for(const host of ['127.0.0.1','entry-package.github.io','jesu-osaka.jp.example.com'])test('review host cannot submit: '+host,()=>{const h=run({host});assert.equal(h.button.disabled,true);let prevented=false,stopped=false;h.listeners.submit({preventDefault:()=>prevented=true,stopImmediatePropagation:()=>stopped=true});assert.ok(prevented&&stopped);});
test('event remains upcoming before the published end',()=>assert.equal(run().status.textContent,undefined));
test('event stops displaying registration after the published end',()=>{const h=run({date:'2026-10-26T13:00:00Z'});assert.equal(h.status.textContent,'日程終了');assert.doesNotMatch(h.link.textContent,/お申し込み/);assert.equal(h.heading.textContent,'掲載イベント');});
test('pages without a form remain supported',()=>assert.doesNotThrow(()=>run({withForm:false})));
