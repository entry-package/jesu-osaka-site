#!/usr/bin/env python3
"""Freeze and publish calendar-only weekly releases; publication is disabled by default."""
import argparse, concurrent.futures, datetime as dt, fcntl, hashlib, importlib.util
import json, re, shutil, subprocess, sys, time, urllib.request
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT.parent
POLICY = ROOT / "ops/weekly-publication.json"
PAGES = ("index.html", "events.html")
ALLOWED = {"content/osaka-events.json", *PAGES}
START, END = "<!-- OSAKA_CALENDAR_START -->", "<!-- OSAKA_CALENDAR_END -->"
PATTERN = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)
PROD_REPO = "entry-package/jesu-osaka-site"
TEST_REPO = "entry-package/jesu-osaka-test-site"
PROD_URL = "https://www.jesu-osaka.jp/"
TEST_URL = "https://entry-package.github.io/jesu-osaka-test-site/"

def call(args, cwd=ROOT):
    return subprocess.check_output([str(x) for x in args], cwd=cwd, text=True).strip()
def git(*args, cwd=ROOT):
    value=subprocess.check_output(["git", *args], cwd=cwd, text=True)
    return value if args and args[0]=="show" else value.strip()
def sha(data): return hashlib.sha256(data).hexdigest()
def read(path): return json.loads(Path(path).read_text())
def write(path, obj):
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n")
def manifest(folder):
    out = {}
    for p in sorted(Path(folder).rglob("*")):
        if p.is_symlink(): raise ValueError("release symlink")
        if p.is_file(): out[str(p.relative_to(folder))] = sha(p.read_bytes())
    return out
def block(text):
    matches = list(PATTERN.finditer(text))
    if len(matches) != 1: raise ValueError("calendar markers must occur exactly once")
    return matches[0].group()
def replace_block(text, new):
    block(text)
    return PATTERN.sub(lambda _: new, text, count=1)
def outside_block(text): return replace_block(text, "[CALENDAR]")
def verify_scope(base, changed):
    if outside_block(base) != outside_block(changed):
        raise ValueError("non-calendar HTML change")
def snapshot(ref, output):
    for row in git("ls-tree", "-r", ref).splitlines():
        info, name = row.split("\t", 1)
        mode, kind, oid = info.split()
        rel = Path(name)
        if mode not in ("100644", "100755") or kind != "blob" or rel.is_absolute() or ".." in rel.parts:
            raise ValueError("unsupported release tree")
        p = output / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(subprocess.check_output(["git", "cat-file", "blob", oid], cwd=ROOT))
def verified_research(data, research, today, previous=None):
    if research.get("schema_version") != 1: raise ValueError("research schema")
    required = {"package", "jesu", "publishers", "teams_creators", "submissions"}
    if set(research.get("discovery", {})) != required or not all(v is True for v in research["discovery"].values()):
        raise ValueError("discovery incomplete")
    receipts = {}
    for r in research.get("sources", []):
        if r["event_id"] in receipts: raise ValueError("duplicate source receipt")
        receipts[r["event_id"]] = r
    for event in data["events"]:
        r = receipts.get(event["id"])
        if not r or r.get("status") not in ("verified", "unavailable"):
            raise ValueError("missing event receipt")
        if r.get("url") != event["official_url"]: raise ValueError("source URL mismatch")
        if event["checked_at"] == today and (r["status"] != "verified" or not r.get("observed_at", "").startswith(today)):
            raise ValueError("unverified fresh date")
    if previous:
        before = {e["id"]:e for e in previous["events"]}
        after = {e["id"]:e for e in data["events"]}
        for eid,event in after.items():
            if event != before.get(eid):
                r=receipts[eid]
                if r["status"] != "verified" or not r.get("observed_at","").startswith(today) or event["checked_at"] != today:
                    raise ValueError("changed event lacks current official verification")
        for eid,event in before.items():
            if eid not in after and any(day >= today for day in event["dates"]):
                r=receipts.get(eid,{})
                if r.get("status") != "verified" or r.get("url") != event["official_url"] or not r.get("observed_at","").startswith(today):
                    raise ValueError("future event removal lacks official verification")
    if data["last_checked"] == today and any(r["status"] != "verified" for r in receipts.values()):
        raise ValueError("full verification date despite source failure")
def stage(work, research_path, output):
    work, output = Path(work).resolve(), Path(output).resolve()
    weekly = (BASE / "weekly").resolve()
    if weekly not in work.parents or weekly not in output.parents or work in output.parents:
        raise ValueError("weekly isolated paths required")
    if output.exists(): raise ValueError("output exists; retain it and use another run")
    source_base = git("rev-parse", "HEAD", cwd=work)
    if git("rev-parse", "HEAD") != source_base: raise ValueError("source base drift")
    changed = set(filter(None, git("diff", "--name-only", "HEAD", cwd=work).splitlines()))
    staged = set(filter(None, git("diff", "--cached", "--name-only", cwd=work).splitlines()))
    if not (changed | staged) <= ALLOWED: raise ValueError("non-calendar source change")
    if git("ls-files", "--others", "--exclude-standard", cwd=work):
        raise ValueError("untracked worktree files; keep research beside release output")
    policy_bytes = (ROOT / "content/event-policy.json").read_bytes()
    if (work / "content/event-policy.json").read_bytes() != policy_bytes: raise ValueError("policy change requires review")
    data = read(work / "content/osaka-events.json")
    verified_research(data, read(research_path), dt.datetime.now(dt.timezone(dt.timedelta(hours=9))).date().isoformat(), json.loads(git("show", source_base + ":content/osaka-events.json", cwd=work)))
    call([sys.executable, "scripts/render-events.py"], work)
    for name in PAGES:
        verify_scope(git("show", source_base + ":" + name, cwd=work), (work/name).read_text())
    call([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test*.py"], work)
    call(["node", "--test", *[str(p.relative_to(work)) for p in sorted((work/"test").glob("*.test.cjs"))]], work)
    git("fetch", "origin", "main")
    baseline = git("rev-parse", "origin/main")
    for name in PAGES:
        if block(git("show", baseline + ":" + name)) != block(git("show", source_base + ":" + name, cwd=work)):
            raise ValueError("published calendar differs from editable baseline; reconcile first")
    output.mkdir(parents=True)
    prod, prev = output/"production", output/"preview"
    prod.mkdir(); snapshot(baseline, prod)
    before = manifest(prod)
    for name in PAGES:
        (prod/name).write_text(replace_block((prod/name).read_text(), block((work/name).read_text())))
    after = manifest(prod)
    changed_release = [name for name in after if after[name] != before[name]]
    if set(before) != set(after) or not set(changed_release) <= set(PAGES): raise ValueError("release scope escaped")
    shutil.copytree(prod, prev)
    (prev/"CNAME").rename(output/"production-CNAME-preserved")
    (prev/"robots.txt").write_text("User-agent: *\nDisallow: /\n")
    for p in prev.glob("*.html"):
        p.write_text(p.read_text().replace('content="index,follow"', 'content="noindex,nofollow"').replace('content="noindex,follow"', 'content="noindex,nofollow"'))
    call([sys.executable, str(work/"scripts/validate.py"), str(prod)], work)
    call([sys.executable, str(work/"scripts/validate.py"), str(prev), "--preview"], work)
    shutil.copy2(research_path, output/"research.json")
    write(output/"candidate.json", {
        "schema_version":1, "id":output.parent.name+"-"+sha(json.dumps(after,sort_keys=True).encode())[:12],
        "source_base":source_base, "source_worktree":str(work), "baseline":baseline,
        "policy_sha256":sha(policy_bytes), "research_sha256":sha((output/"research.json").read_bytes()),
        "production":after, "preview":manifest(prev), "changed_files":changed_release,
        "data_sha256":sha((work/"content/osaka-events.json").read_bytes()),
        "publication":"pending_owner_authorization", "test_fixture":read(research_path).get("test_fixture",False)})
    return read(output/"candidate.json")
def verify_candidate(folder):
    c = read(folder/"candidate.json")
    if c.get("schema_version") != 1 or not re.fullmatch(r"[a-zA-Z0-9_-]{1,100}", c.get("id","")):
        raise ValueError("invalid candidate")
    if manifest(folder/"production") != c["production"] or manifest(folder/"preview") != c["preview"]:
        raise ValueError("frozen artifact changed")
    if sha((folder/"research.json").read_bytes()) != c["research_sha256"]: raise ValueError("research changed")
    if sha((ROOT/"content/event-policy.json").read_bytes()) != c["policy_sha256"]: raise ValueError("listing policy drift")
    if sha((Path(c["source_worktree"])/"content/osaka-events.json").read_bytes()) != c["data_sha256"]:
        raise ValueError("source data drift")
    git("fetch","origin","main")
    if git("rev-parse","origin/main") != c["baseline"]: raise ValueError("production advanced")
    if git("rev-parse","HEAD") != c["source_base"]: raise ValueError("editable source advanced")
    work=Path(c["source_worktree"]).resolve()
    if (BASE/"weekly").resolve() not in work.parents or git("rev-parse","HEAD",cwd=work) != c["source_base"]:
        raise ValueError("untrusted source worktree")
    if set(filter(None,git("diff","--name-only","HEAD",cwd=work).splitlines())) - ALLOWED:
        raise ValueError("source code changed after freeze")
    for row in git("ls-tree","-r",c["baseline"]).splitlines():
        info,name=row.split("\t",1)
        if name not in c["production"]: raise ValueError("baseline file removed")
        expected=subprocess.check_output(["git","show",c["baseline"]+":"+name],cwd=ROOT)
        actual=(folder/"production"/name).read_bytes()
        if name in PAGES:
            verify_scope(expected.decode(),actual.decode())
            if block(actual.decode()) != block((work/name).read_text()): raise ValueError("calendar frozen content mismatch")
        elif expected != actual: raise ValueError("non-calendar release changed")
    actual_changed=[name for name in c["production"] if sha(subprocess.check_output(["git","show",c["baseline"]+":"+name],cwd=ROOT)) != c["production"][name]]
    if sorted(actual_changed) != sorted(c["changed_files"]) or not set(actual_changed)<=set(PAGES): raise ValueError("changed file list mismatch")
    baseline_names=set(git("ls-tree","-r","--name-only",c["baseline"]).splitlines())
    if baseline_names != set(c["production"]): raise ValueError("release files added")
    if set(c["preview"]) != set(c["production"])-{"CNAME"}: raise ValueError("preview file set changed")
    for name in c["preview"]:
        prod=(folder/"production"/name).read_bytes()
        if name=="robots.txt": prod=b"User-agent: *\nDisallow: /\n"
        elif name.endswith(".html"):
            prod=prod.replace(b'content="index,follow"',b'content="noindex,nofollow"').replace(b'content="noindex,follow"',b'content="noindex,nofollow"')
        if prod != (folder/"preview"/name).read_bytes(): raise ValueError("preview differs from production")
    if c.get("test_fixture",False) != read(folder/"research.json").get("test_fixture",False): raise ValueError("fixture marker mismatch")
    data=read(work/"content/osaka-events.json")
    verified_research(data,read(folder/"research.json"),dt.datetime.now(dt.timezone(dt.timedelta(hours=9))).date().isoformat(),json.loads(git("show",c["source_base"]+":content/osaka-events.json")))
    return c
def enabled(policy):
    return policy.get("enabled") is True and policy.get("scope") == "calendar-only" and bool(policy.get("owner_authorization_ref"))
def check_live(url, files):
    def check(item):
        name, digest = item
        with urllib.request.urlopen(urllib.request.Request(url+name, headers={"Cache-Control":"no-cache"}), timeout=30) as res:
            b=res.read()
            if res.status != 200 or sha(b) != digest: raise ValueError("public artifact mismatch: "+name)
        return name
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool: return list(pool.map(check, files.items()))
def wait_pages(repo, commit):
    for _ in range(48):
        r=json.loads(call(["gh","api","repos/"+repo+"/pages/builds/latest"]))
        if r.get("commit")==commit and r.get("status")=="built": return
        if r.get("commit")==commit and r.get("status")=="errored": raise ValueError("Pages failed")
        time.sleep(5)
    raise TimeoutError("Pages build not verified")
def publish_tree(repo, folder, frozen, baseline, branch, production=False):
    git("fetch", "https://github.com/"+repo+".git", "main")
    current=git("rev-parse","FETCH_HEAD")
    if baseline and current != baseline: raise ValueError("upstream changed")
    work=folder/("publish-production" if production else "publish-preview")
    git("worktree","add","-b",branch,str(work),current)
    backup=folder/("before-production" if production else "before-preview");backup.mkdir()
    for p in work.iterdir():
        if p.name != ".git": shutil.move(str(p),backup/p.name)
    for p in frozen.iterdir():
        if p.is_dir(): shutil.copytree(p,work/p.name)
        else: shutil.copy2(p,work/p.name)
    git("add","-A",cwd=work)
    git("commit","-m","Weekly official Osaka event calendar update",cwd=work)
    release=git("rev-parse","HEAD",cwd=work)
    remote="https://github.com/"+repo+".git"
    if not production:
        git("push",remote,"HEAD:main",cwd=work);return release
    git("push",remote,"HEAD:"+branch,cwd=work)
    body=folder/"pr-body.md"
    body.write_text("週次の公式情報照合に基づき、府内イベントカレンダー欄のみを更新。写真・レポート・CSS・フォームは変更なし。\n\n"+TEST_URL+" で同一内容の公開ファイルを全件SHA256照合済み。基準コミット "+current+"、候補 "+folder.name+"。\n")
    pr=call(["gh","pr","create","--repo",repo,"--base","main","--head",branch,"--title","府内公式イベントカレンダーの週次更新","--body-file",str(body)],work)
    info=json.loads(call(["gh","pr","view",pr,"--repo",repo,"--json","baseRefOid,headRefOid"]))
    if info["baseRefOid"] != current or info["headRefOid"] != release: raise ValueError("PR race")
    call(["gh","pr","merge",pr,"--repo",repo,"--merge","--match-head-commit",release],work)
    return json.loads(call(["gh","pr","view",pr,"--repo",repo,"--json","mergeCommit"]))["mergeCommit"]["oid"]
def publish(folder, dry_run=False):
    folder=Path(folder).resolve()
    if (BASE/"weekly").resolve() not in folder.parents: raise ValueError("candidate outside weekly storage")
    with (BASE/"weekly-publication.lock").open("a") as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        c=verify_candidate(folder)
        policy=read(POLICY)
        if dry_run:return {"valid":True,"changed_files":c["changed_files"],"publication_enabled":enabled(policy),"dry_run":True}
        if c.get("test_fixture"):raise PermissionError("test fixtures cannot be published")
        if not enabled(policy):raise PermissionError("weekly publication requires explicit standing authorization; no public mutation")
        if not c["changed_files"]:return {"publication":"no_change","candidate":c["id"]}
        if (folder/"publication-started.json").exists():raise ValueError("publication previously started; reconcile before retry")
        write(folder/"publication-started.json",{"candidate":c["id"],"baseline":c["baseline"]})
        branch="calendar/weekly-"+c["id"]
        pre=publish_tree(TEST_REPO,folder,folder/"preview",None,"preview/"+c["id"])
        wait_pages(TEST_REPO,pre);check_live(TEST_URL,c["preview"])
        verify_candidate(folder)
        prod=publish_tree(PROD_REPO,folder,folder/"production",c["baseline"],branch,True)
        wait_pages(PROD_REPO,prod);check_live(PROD_URL,c["production"])
        work=Path(c["source_worktree"])
        git("add","content/osaka-events.json",*PAGES,cwd=work)
        if git("diff","--cached","--name-only",cwd=work):
            git("commit","-m","Keep published weekly calendar as next editable baseline",cwd=work)
        imported=False
        if git("rev-parse","HEAD")==c["source_base"] and not git("status","--porcelain"):
            git("merge","--ff-only",git("rev-parse","HEAD",cwd=work));imported=True
        result={"publication":"verified","preview_commit":pre,"production_commit":prod,"source_imported":imported,"url":PROD_URL}
        write(folder/"publication.json",result);return result
def main():
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest="command",required=True)
    s=sub.add_parser("stage");s.add_argument("--worktree",required=True);s.add_argument("--research",required=True);s.add_argument("--output",required=True)
    s=sub.add_parser("publish");s.add_argument("--candidate",required=True);s.add_argument("--dry-run",action="store_true")
    args=p.parse_args()
    result=stage(args.worktree,args.research,args.output) if args.command=="stage" else publish(args.candidate,args.dry_run)
    print(json.dumps(result,ensure_ascii=False))
if __name__=="__main__":main()
