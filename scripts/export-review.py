#!/usr/bin/env python3
"""Export offline review pages; embedded images, CSS and scripts. No network sends."""
from pathlib import Path
import argparse,base64,mimetypes,re,shutil
p=argparse.ArgumentParser();p.add_argument('release',type=Path);p.add_argument('output',type=Path);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
for source in a.release.glob('*.html'):
 text=source.read_text()
 text=text.replace('<link rel="stylesheet" href="./styles.css" />','<style>'+ (a.release/'styles.css').read_text()+'</style>')
 text=re.sub(r'<script src="\./(site.js|contact-submit.js)" defer></script>',lambda m:'<script>document.addEventListener("DOMContentLoaded", () => {\n'+ (a.release/m[1]).read_text()+'\n});</script>',text)
 def inline(m):
  path=a.release/m[2].removeprefix('./');mime=mimetypes.guess_type(path)[0] or 'application/octet-stream'
  return m[1]+'data:'+mime+';base64,'+base64.b64encode(path.read_bytes()).decode()+m[3]
 text=re.sub(r'((?:src|href)=")([^"\n]+\.(?:png|jpg))(")',inline,text)
 if source.name=='contact.html':
  text=re.sub(r'action="https://script.google.com/[^"]+"','action="#"',text)
  text=text.replace('<button type="submit"','<button disabled type="submit"')
 (a.output/source.name).write_text(text)
(a.output/'.keep-local').write_text('社長によるデザイン確認待ち。クラウド原本照合後も確認完了まで保持。\n')
(a.output/'assets/documents').mkdir(parents=True,exist_ok=True)
shutil.copy2(a.release/'assets/documents/jesu-osaka-guide.pdf',a.output/'assets/documents/jesu-osaka-guide.pdf')
print(a.output)
