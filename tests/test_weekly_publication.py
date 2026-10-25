import copy,datetime as dt,importlib.util,json,subprocess,tempfile,unittest
from pathlib import Path
from unittest import mock
ROOT=Path(__file__).resolve().parents[1]
def module(name,file):
    spec=importlib.util.spec_from_file_location(name,ROOT/"scripts"/file)
    obj=importlib.util.module_from_spec(spec);spec.loader.exec_module(obj);return obj
release=module("weekly_release","weekly-release.py")
prep=module("prepare_weekly","prepare-weekly.py")
class CalendarPublicationTests(unittest.TestCase):
    def test_reject_noncalendar_html_change(self):
        a="header"+release.START+"old"+release.END+"footer"
        release.verify_scope(a,a.replace("old","new"))
        with self.assertRaises(ValueError):release.verify_scope(a,a.replace("header","changed"))
    def test_duplicate_markers_rejected(self):
        with self.assertRaises(ValueError):release.block((release.START+"x"+release.END)*2)
    def test_publication_disabled_until_explicit_receipt(self):
        self.assertFalse(release.enabled({"enabled":True,"scope":"calendar-only","owner_authorization_ref":None}))
        self.assertFalse(release.enabled({"enabled":False,"scope":"calendar-only","owner_authorization_ref":"reviewed-owner-reference"}))
        self.assertFalse(release.enabled({"enabled":True,"scope":"whole-site","owner_authorization_ref":"reviewed-owner-reference"}))
    def test_workflow_omits_only_empty_jekyll_marker(self):
        files={".nojekyll":release.sha(b""),"index.html":release.sha(b"page")}
        self.assertEqual(release.public_files(files,"workflow"),{"index.html":files["index.html"]})
        self.assertEqual(release.public_files(files,"legacy"),files)
    def test_workflow_rejects_unexpected_hidden_or_nonempty_control_file(self):
        for files in ({".nojekyll":release.sha(b"content")},{".hidden/data.json":release.sha(b"data")}):
            with self.assertRaises(ValueError):release.public_files(files,"workflow")
        with self.assertRaises(ValueError):release.public_files({},"unknown")
    def test_workflow_still_rejects_changed_public_asset(self):
        response=mock.MagicMock();response.__enter__.return_value=response
        response.status=200;response.read.return_value=b"changed"
        with mock.patch.object(release.urllib.request,"urlopen",return_value=response):
            with self.assertRaisesRegex(ValueError,"public artifact mismatch: index.html"):
                release.check_live("https://example.com/",{".nojekyll":release.sha(b""),"index.html":release.sha(b"approved")},"workflow")
    def test_pages_wait_reports_verified_build_type(self):
        completed={"head_sha":"abc","head_branch":"main","status":"completed","conclusion":"success"}
        workflow=mock.Mock(returncode=0,stdout=json.dumps({"workflow_runs":[completed]}))
        with mock.patch.object(release.subprocess,"run",return_value=workflow):
            self.assertEqual(release.wait_pages("owner/repo","abc"),"workflow")
        missing=mock.Mock(returncode=1,stderr="HTTP 404")
        with mock.patch.object(release.subprocess,"run",return_value=missing),mock.patch.object(release,"call",return_value=json.dumps({"commit":"abc","status":"built"})):
            self.assertEqual(release.wait_pages("owner/repo","abc"),"legacy")
    def records(self):
        event={"id":"example","official_url":"https://example.com/event","checked_at":"2026-10-20","dates":["2026-10-30"],"name":"Old"}
        data={"events":[event],"last_checked":"2026-10-20"}
        research={"schema_version":1,"discovery":{k:True for k in ("package","jesu","publishers","teams_creators","submissions")},
          "sources":[{"event_id":"example","url":event["official_url"],"status":"unavailable","observed_at":"2026-10-21T09:00:00+09:00"}]}
        return data,research
    def test_failed_source_keeps_previous_fact_but_cannot_change_event(self):
        previous,research=self.records();updated=copy.deepcopy(previous)
        release.verified_research(updated,research,"2026-10-21",previous)
        updated["events"][0]["name"]="Changed"
        with self.assertRaises(ValueError):release.verified_research(updated,research,"2026-10-21",previous)
    def test_unverified_all_checked_date_rejected(self):
        data,research=self.records();data["last_checked"]="2026-10-21"
        with self.assertRaises(ValueError):release.verified_research(data,research,"2026-10-21")
    def test_future_removal_needs_evidence(self):
        previous,research=self.records();updated=copy.deepcopy(previous);updated["events"]=[]
        with self.assertRaises(ValueError):release.verified_research(updated,research,"2026-10-21",previous)
    def test_git_show_preserves_html_newlines_for_scope_check(self):
        with tempfile.TemporaryDirectory() as td:
            repo=Path(td)
            subprocess.run(["git","init","-b","source",str(repo)],check=True,capture_output=True)
            original="header\n"+release.START+"old"+release.END+"footer\n"
            (repo/"index.html").write_text(original)
            subprocess.run(["git","-C",str(repo),"add","index.html"],check=True)
            subprocess.run(["git","-C",str(repo),"-c","user.name=Test","-c","user.email=test@example.com","commit","-m","baseline"],check=True,capture_output=True)
            actual=release.git("show","HEAD:index.html",cwd=repo)
            self.assertEqual(actual,original)
            release.verify_scope(actual,original.replace("old","new"))
    def test_worktree_reuse_does_not_relabel_its_base(self):
        with tempfile.TemporaryDirectory() as td:
            repo=Path(td)/"repo";repo.mkdir()
            subprocess.run(["git","init","-b","source",str(repo)],check=True,capture_output=True)
            def git(*args):return subprocess.check_output(["git","-C",str(repo),*args],text=True).strip()
            (repo/"file").write_text("first");git("add","file");git("-c","user.name=Test","-c","user.email=test@example.com","commit","-m","first")
            now=dt.datetime(2026,10,21,9,tzinfo=dt.timezone(dt.timedelta(hours=9)))
            first=prep.prepare(repo,now=now)
            (repo/"file").write_text("second");git("add","file");git("-c","user.name=Test","-c","user.email=test@example.com","commit","-m","second")
            again=prep.prepare(repo,now=now)
            self.assertEqual(first["base_sha"],again["base_sha"])
            self.assertNotEqual(again["base_sha"],git("rev-parse","HEAD"))
            manual=prep.prepare(repo,manual=True,now=now)
            self.assertEqual(manual["trigger"],"manual")
            self.assertNotEqual(manual["run_id"],first["run_id"])
            self.assertEqual(manual["base_sha"],git("rev-parse","HEAD"))
if __name__=="__main__":unittest.main()
