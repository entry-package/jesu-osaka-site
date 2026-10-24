#!/usr/bin/env python3
"""Verify the release graph, metadata, and preservation of form protections."""
import argparse,json,re,subprocess,sys
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
class Page(HTMLParser):
 def __init__(self,text):
  super().__init__();self.ids=[];self.refs=[];self.robots=[];self.h1=0;self.forms=[];self.text=[];self.feed(text)
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if 'id' in a:self.ids.append(a['id'])
  if tag=='h1':self.h1+=1
  if tag=='meta' and a.get('name')=='robots':self.robots.append(a.get('content'))
  if tag=='form':self.forms.append(a)
  for key in ('src','href'):
   if a.get(key):self.refs.append(a[key])
 def handle_data(self,data):self.text.append(data)
def validate(root,preview):
 runtime=Path.home()/'.local/share/site-image-gate/venv/bin/python'
 subprocess.run([str(runtime) if runtime.is_file() else sys.executable,str(Path(__file__).resolve().parents[1]/'.article-images/gate.py'),'--root',str(root)],check=True)
 errors=[];pages={f.name:Page(f.read_text()) for f in root.glob('*.html')};count=0
 for name,page in pages.items():
  if page.h1!=1:errors.append(f'{name}: expected exactly one h1')
  if len(page.ids)!=len(set(page.ids)):errors.append(f'{name}: duplicate ids')
  expected='noindex,nofollow' if preview else ('noindex,follow' if name=='contact-thanks.html' else 'index,follow')
  if page.robots!=[expected]:errors.append(f'{name}: incorrect robots')
  for ref in page.refs:
   u=urlsplit(ref)
   if u.scheme or u.netloc:continue
   path=unquote(u.path).removeprefix('./') or name
   target=root/path
   if not target.is_file():errors.append(f'{name}: missing {ref}')
   elif u.fragment and target.suffix=='.html' and u.fragment not in pages[target.name].ids:errors.append(f'{name}: missing anchor {ref}')
   count+=1
  if re.search('現行サイト|再構成しています|カード形式へ整理|本日開催|当日のお申込みも', ''.join(page.text)):errors.append(f'{name}: stale copy')
 form=pages['contact.html'].forms
 if len(form)!=1 or not form[0].get('action','').startswith('https://script.google.com/macros/s/') or form[0].get('method')!='post':errors.append('contact receiver changed')
 for key in ('name="website"','name="ts"','name="requestId"','maxlength="4000"','contact-submit.js'):
  if key not in (root/'contact.html').read_text():errors.append('missing form control '+key)
 if errors:raise SystemExit('\n'.join(errors))
 print(json.dumps({'pages':len(pages),'local_links_and_assets':count,'preview':preview,'errors':0},ensure_ascii=False))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('--preview',action='store_true');a=p.parse_args();validate(a.root,a.preview)
