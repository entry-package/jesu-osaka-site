import copy,importlib.util,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("events",ROOT/"scripts/render-events.py");mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
class EventPolicyTests(unittest.TestCase):
 def setUp(self):
  self.data=json.loads((ROOT/"content/osaka-events.json").read_text());self.policy=json.loads((ROOT/"content/event-policy.json").read_text())
 def rejects(self,mutate):
  mutate(self.data["events"][0])
  with self.assertRaises(ValueError):mod.validate(self.data,self.policy)
 def test_verified_events(self):mod.validate(self.data,self.policy)
 def test_reject_outside_osaka(self):self.rejects(lambda e:e.update(prefecture="兵庫県"))
 def test_reject_online_only(self):self.rejects(lambda e:e.update(format="online"))
 def test_reject_nonofficial_and_host_spoof(self):self.rejects(lambda e:e.update(official_url="https://redee.co.jp.example.com/event"))
 def test_partial_recheck_may_be_newer_than_last_complete_check(self):
  self.data["last_checked"]="2026-10-19"
  mod.validate(self.data,self.policy)
 def test_reject_duplicate_event_slot(self):
  x=copy.deepcopy(self.data["events"][0]);x["id"]="duplicate";self.data["events"].append(x)
  with self.assertRaises(ValueError):mod.validate(self.data,self.policy)
 def test_reject_unconfirmed_large_creator_event(self):self.rejects(lambda e:e.update(category="creator",importance={"kind":"team_creator_major","evidence_url":e["official_url"]}))
 def test_no_intermediate_dates(self):
  text=mod.render(self.data,self.policy,"test-")
  self.assertIn('2026-11-07',text)
  self.assertNotIn('2026-11-09 第5回',text)
 def test_ended_dates_leave_upcoming_without_data_loss(self):
  self.data["last_checked"]="2027-01-01"
  self.assertEqual(mod.active_events(self.data,self.policy),[])
  self.assertEqual(len(self.data["events"]),5)
 def test_postponed_unknown_date_is_not_scheduled(self):
  self.data["events"][0]["status"]="postponed"
  self.assertNotIn(self.data["events"][0],mod.active_events(self.data,self.policy))
if __name__=="__main__":unittest.main()
