import copy,importlib.util,json,re,unittest,datetime as dt
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("events",ROOT/"scripts/render-events.py");mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
class EventPolicyTests(unittest.TestCase):
 def setUp(self):
  self.data=json.loads((ROOT/"content/osaka-events.json").read_text());self.policy=json.loads((ROOT/"content/event-policy.json").read_text())
 def rejects(self,mutate):
  mutate(self.data["events"][0])
  with self.assertRaises(ValueError):mod.validate(self.data,self.policy)
 def test_own_seminar_has_current_month_marker_without_duplicate_detail_card(self):
  text=mod.render(self.data,self.policy,"home-")
  self.assertIn('2026年10月 府内のイベント予定',text)
  self.assertIn('href="#jesu-seminar-vol2"',text)
  self.assertNotIn('id="home-jesu-seminar-vol2-2026"',text)
 def test_external_seminar_cannot_use_jesu_exception(self):
  self.rejects(lambda e:e.update(activity_type="seminar"))
 def test_verified_events(self):mod.validate(self.data,self.policy)
 def test_reject_outside_osaka(self):self.rejects(lambda e:e.update(prefecture="兵庫県"))
 def test_reject_online_only(self):self.rejects(lambda e:e.update(format="online"))
 def test_reject_nonofficial_and_host_spoof(self):self.rejects(lambda e:e.update(official_url="https://redee.co.jp.example.com/event"))
 def test_partial_recheck_may_be_newer_than_last_complete_check(self):
  self.data["last_checked"]="2026-10-19"
  mod.validate(self.data,self.policy)
 def test_reject_exhibition_without_gameplay(self):self.rejects(lambda e:e.update(activity_type="exhibition"))
 def test_reject_duplicate_event_slot(self):
  x=copy.deepcopy(self.data["events"][0]);x["id"]="duplicate";self.data["events"].append(x)
  with self.assertRaises(ValueError):mod.validate(self.data,self.policy)
 def test_reject_unconfirmed_large_creator_event(self):self.rejects(lambda e:e.update(category="creator",importance={"kind":"team_creator_major","evidence_url":e["official_url"]}))
 def test_package_small_meetup_allowed(self):
  e=copy.deepcopy(next(x for x in self.data["events"] if x.get("importance",{}).get("kind")=="package_related"));e["capacity"]=10;e["activity_type"]="meetup"
  mod.validate({**self.data,"events":[e]},self.policy)
 def test_package_future_announcement_not_lost_after_180_days(self):
  e=copy.deepcopy(next(x for x in self.data["events"] if x.get("importance",{}).get("kind")=="package_related"));e["dates"]=["2028-01-01"]
  self.assertEqual(mod.active_events({**self.data,"events":[e]},self.policy),[e])
 def test_official_package_post_can_confirm_relation(self):
  e=copy.deepcopy(next(x for x in self.data["events"] if x.get("importance",{}).get("kind")=="package_related"));e["package_relation"]["evidence_url"]="https://x.com/PACkage_2018/status/2112455182881833371"
  mod.validate({**self.data,"events":[e]},self.policy)
 def test_other_accounts_cannot_confirm_package_relation(self):
  e=copy.deepcopy(next(x for x in self.data["events"] if x.get("importance",{}).get("kind")=="package_related"));e["package_relation"]["evidence_url"]="https://x.com/another_account/status/2112455182881833371"
  with self.assertRaises(ValueError):mod.validate({**self.data,"events":[e]},self.policy)
 def test_package_relation_is_required(self):
  e=copy.deepcopy(next(x for x in self.data["events"] if x.get("importance",{}).get("kind")=="package_related"));e.pop("package_relation")
  with self.assertRaises(ValueError):mod.validate({**self.data,"events":[e]},self.policy)
 def test_external_cannot_use_package_exception(self):
  e=copy.deepcopy(self.data["events"][0]);e["importance"]["kind"]="package_related"
  with self.assertRaises(ValueError):mod.validate({**self.data,"events":[e]},self.policy)
 def test_no_intermediate_dates(self):
  text=mod.render(self.data,self.policy,"test-")
  self.assertIn('2026-11-07',text)
  self.assertNotIn('2026-11-09 第5回',text)
 def test_ended_dates_leave_upcoming_without_data_loss(self):
  count=len(self.data["events"])
  latest=max(dt.date.fromisoformat(d) for e in self.data["events"] for d in e["dates"])
  self.data["last_checked"]=(latest+dt.timedelta(days=1)).isoformat()
  self.assertEqual(mod.active_events(self.data,self.policy),[])
  self.assertEqual(len(self.data["events"]),count)
 def test_postponed_unknown_date_is_not_scheduled(self):
  self.data["events"][0]["status"]="postponed"
  self.assertNotIn(self.data["events"][0],mod.active_events(self.data,self.policy))
 def test_static_default_only_includes_jesu_involved_without_padding(self):
  text=mod.render(self.data,self.policy,"home-",today="2026-10-25")
  visible=re.findall(r'<article[^>]*data-calendar-item="([^"]+)"(?! hidden)>',text)
  self.assertEqual(visible,["jesu-seminar-vol2-2026"])
  self.assertIn('data-calendar-item="spaworld-halloween-digital-2026" hidden',text)
  after=mod.render(self.data,self.policy,"home-",today="2026-10-27")
  self.assertEqual(re.findall(r'<article[^>]*data-calendar-item="([^"]+)"(?! hidden)>',after),[])
  self.assertIn('data-calendar-empty>',after)
 def test_jesu_involvement_matches_existing_editorial_scope(self):
  spec=importlib.util.spec_from_file_location("sns",ROOT/"scripts/queue-calendar-sns.py")
  sns=importlib.util.module_from_spec(spec);spec.loader.exec_module(sns)
  fixtures=self.data["events"]+[
   {"category":"jesu","organizer":"外部主催者"},
   {"category":"jesu","organizer":"一般社団法人日本eスポーツ連合"},
   *({"category":"corporate","jesu_role":role} for role in ("主催","共催","運営","後援","協力","来場")),
  ]
  for event in fixtures:self.assertEqual(mod.jesu_involved(event),sns.jesu_involved(event))
if __name__=="__main__":unittest.main()
