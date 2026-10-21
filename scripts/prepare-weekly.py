#!/usr/bin/env python3
"""Create isolated weekly worktrees and retain the original base on reuse."""
import argparse, datetime as dt, fcntl, json, subprocess
from pathlib import Path
HOME=Path.home(); REPO=HOME/".local/share/jesu-osaka/repo"
def prepare(repo=REPO, manual=False, now=None):
    repo=Path(repo).resolve()
    now=now or dt.datetime.now(dt.timezone(dt.timedelta(hours=9)))
    date=now.strftime("%Y%m%d")
    run_id=("manual-"+now.strftime("%Y%m%dT%H%M%S%f")) if manual else date
    root=repo.parent/"weekly"; root.mkdir(parents=True,exist_ok=True)
    def git(*args,cwd=repo):
        return subprocess.check_output(["git","-C",str(cwd),*args],text=True).strip()
    with (root/"prepare.lock").open("a") as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        run=root/run_id; work=run/"worktree"; context_file=run/"context.json"
        if context_file.exists():
            context=json.loads(context_file.read_text())
            if Path(context["worktree"]).resolve()!=work.resolve():
                raise ValueError("stored worktree mismatch")
            if git("rev-parse","--git-common-dir",cwd=work) != git("rev-parse","--git-common-dir"):
                # Git may return absolute common-dir for a worktree and .git for repo.
                common=Path(git("rev-parse","--git-common-dir",cwd=work)).resolve()
                original=(repo/git("rev-parse","--git-common-dir")).resolve()
                if common != original:raise ValueError("different git repository")
            subprocess.run(["git","-C",str(work),"merge-base","--is-ancestor",context["base_sha"],"HEAD"],check=True)
            return dict(context,reused=True)
        if work.exists():raise ValueError("worktree without original context; reconcile first")
        if git("status","--porcelain"):raise ValueError("editable source must be committed before preparing a weekly run")
        sha=git("rev-parse","HEAD");branch="calendar/weekly-"+run_id
        run.mkdir(parents=True,exist_ok=True)
        subprocess.run(["git","-C",str(repo),"worktree","add","-b",branch,str(work),sha],check=True)
        context={"date":date,"run_id":run_id,"base_branch":git("branch","--show-current"),
                 "base_sha":sha,"worktree":str(work),"output":str(run/"review"),
                 "approval":"pending","publication":"not_authorized",
                 "trigger":"manual" if manual else "unverified","created_at":now.isoformat()}
        context_file.write_text(json.dumps(context,indent=2)+"\n")
        return context
def main():
    p=argparse.ArgumentParser();p.add_argument("--manual",action="store_true");a=p.parse_args()
    print(json.dumps(prepare(manual=a.manual)))
if __name__=="__main__":main()
