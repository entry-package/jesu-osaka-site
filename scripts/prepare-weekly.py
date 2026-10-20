#!/usr/bin/env python3
"""Create isolated weekly worktree; never fetches, pushes or deploys."""
import datetime as dt,json,subprocess
from pathlib import Path
HOME=Path.home();REPO=HOME/".local/share/jesu-osaka/repo";BASE=REPO.parent
date=dt.datetime.now(dt.timezone(dt.timedelta(hours=9))).strftime("%Y%m%d")
run=BASE/"weekly"/date;run.mkdir(parents=True,exist_ok=True)
def git(*args):return subprocess.check_output(["git","-C",str(REPO),*args],text=True).strip()
main_has=subprocess.run(["git","-C",str(REPO),"cat-file","-e","main:content/osaka-events.json"],capture_output=True).returncode==0
base="main" if main_has else "design/jesu-refresh-20261020"
sha=git("rev-parse",base);work=run/"worktree";branch="calendar/weekly-"+date
if not work.exists():subprocess.run(["git","-C",str(REPO),"worktree","add","-b",branch,str(work),base],check=True)
context={"date":date,"base_branch":base,"base_sha":sha,"worktree":str(work),"output":str(run/"review"),"approval":"pending","publication":"not_authorized"}
(run/"context.json").write_text(json.dumps(context,indent=2)+"\n")
print(json.dumps(context))
