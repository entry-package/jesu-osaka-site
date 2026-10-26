import copy,importlib.util,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location("events_named",ROOT/"scripts/render-events.py");m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class NamedException(unittest.TestCase):
 def test_only_the_requested_event_is_accepted(self):
  data=json.loads((ROOT/"content/osaka-events.json").read_text());policy=json.loads((ROOT/"content/event-policy.json").read_text())
  e=copy.deepcopy(next(x for x in data["events"] if x["id"]=="joshin-kishiwada-20261123"))
  m.validate({**data,"events":[e]},policy);self.assertFalse(m.jesu_involved(e))
  for field,value in (("id","unrelated-event"),("dates",["2026-11-24"]),("venue","別会場")):
   with self.assertRaises(ValueError):m.validate({**data,"events":[{**e,field:value}]},policy)
