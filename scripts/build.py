#!/usr/bin/env python3
"""Create an isolated, deterministic static release; never deploys."""
import argparse, hashlib, json, shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PAGES=['index.html','news.html','events.html','joshin-news.html','contact.html','contact-thanks.html']
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);parser.add_argument('--preview',action='store_true');args=parser.parse_args()
 out=Path(args.output).expanduser().resolve()
 if out==ROOT or ROOT in out.parents: raise SystemExit('Output must be outside source checkout')
 out.mkdir(parents=True,exist_ok=True)
 if any(out.iterdir()): raise SystemExit('Output must be empty to avoid stale release files')
 for name in PAGES+['styles.css','site.js','contact-submit.js','sitemap.xml','.nojekyll','CNAME']:
  if args.preview and name=='CNAME': continue
  body=(ROOT/name).read_bytes()
  if args.preview and name in PAGES: body=body.replace(b'content="index,follow"',b'content="noindex,nofollow"').replace(b'content="noindex,follow"',b'content="noindex,nofollow"')
  (out/name).write_bytes(body)
 shutil.copytree(ROOT/'assets',out/'assets')
 (out/'robots.txt').write_text('User-agent: *\nDisallow: /\n' if args.preview else 'User-agent: *\nAllow: /\nSitemap: https://www.jesu-osaka.jp/sitemap.xml\n')
 manifest={str(f.relative_to(out)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(out.rglob('*')) if f.is_file()}
 print(json.dumps({'output':str(out),'preview':args.preview,'file_count':len(manifest),'sha256':hashlib.sha256(json.dumps(manifest,sort_keys=True).encode()).hexdigest(),'files':manifest},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
