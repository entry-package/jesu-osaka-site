import datetime as dt, importlib.util, tempfile, unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location("queue_sns",Path(__file__).resolve().parents[1]/"scripts/queue-calendar-sns.py")
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class CalendarSns(unittest.TestCase):
    def setUp(self):
        self.now=dt.datetime.fromisoformat("2026-10-21T14:00:00+09:00")
        self.html=m.START+"published"+m.END
        self.data={"events":[{"id":"a","name":"Official event","category":"jesu","organizer":"JeSU大阪","dates":["2026-10-24"],"status":"scheduled","venue":"Osaka","official_url":"https://example.org/event","checked_at":"2026-10-20"}]}
    def make(self): return m.source(self.data,self.html,self.html,self.now)
    def test_only_published_calendar(self):
        with self.assertRaises(ValueError): m.source(self.data,self.html,self.html.replace("published","old"),self.now)
    def test_synthetic_rejected(self):
        self.data["test_fixture"]=True
        with self.assertRaises(ValueError): self.make()
    def test_weekly_identity_and_expiry(self):
        s=self.make();self.assertTrue(s["url"].endswith("week=2026-10-19"))
        self.assertEqual(s["expires_at"],"2026-10-26T00:00:00+09:00")
        self.now+=dt.timedelta(days=7);self.assertTrue(self.make()["url"].endswith("week=2026-10-26"))
    def test_dates_do_not_become_fresh_official_verification(self):
        s=self.make();self.assertEqual(s["receipt"]["event_verification_dates"]["a"],"2026-10-20")
        self.assertEqual(s["receipt"]["kind"],"published_calendar_readback")
    def test_finished_and_cancelled_not_promoted(self):
        self.data["events"][0]["status"]="cancelled";self.assertEqual(len(self.make()["facts"]),1)
    def test_package_involvement_alone_is_not_promoted(self):
        self.data["events"][0].update(category="corporate",organizer="株式会社PACkage")
        s=self.make()
        self.assertEqual([fact["id"] for fact in s["facts"]],["calendar"])
        self.assertEqual(s["receipt"]["event_verification_dates"],{})
    def test_jesu_category_without_involvement_is_not_promoted(self):
        self.data["events"][0]["organizer"]="External organizer"
        self.assertEqual([fact["id"] for fact in self.make()["facts"]],["calendar"])
    def test_duplicate_markers_rejected(self):
        with self.assertRaises(ValueError):m.calendar_block(self.html+self.html)
if __name__=="__main__":unittest.main()
