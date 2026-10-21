#!/usr/bin/env python3
"""Transfer a published calendar to the existing SNS drafting inbox; never sends."""
import argparse, datetime as dt, hashlib, importlib.util, json, re, sys, urllib.request
from pathlib import Path
from zoneinfo import ZoneInfo
ROOT = Path(__file__).resolve().parents[1]
JST = ZoneInfo("Asia/Tokyo")
URL = "https://www.jesu-osaka.jp/events.html"
START, END = "<!-- OSAKA_CALENDAR_START -->", "<!-- OSAKA_CALENDAR_END -->"

def calendar_block(html):
    found = re.findall(re.escape(START) + r".*?" + re.escape(END), html, re.S)
    if len(found) != 1: raise ValueError("exactly one calendar block required")
    return found[0]

def source(data, local_html, live_html, now):
    if now.tzinfo is None: raise ValueError("timezone required")
    now = now.astimezone(JST)
    if data.get("test_fixture"): raise ValueError("synthetic data cannot enter editorial inbox")
    if calendar_block(local_html) != calendar_block(live_html):
        raise ValueError("calendar not published or live source drift")
    monday = now.date() - dt.timedelta(days=now.weekday())
    expiry = dt.datetime.combine(monday + dt.timedelta(days=7), dt.time(), JST)
    upcoming = []
    for event in data["events"]:
        dates = [day for day in event["dates"] if now.date().isoformat() <= day <= (now.date()+dt.timedelta(days=30)).isoformat()]
        if not dates or event["status"] != "scheduled": continue
        upcoming.append({"id":event["id"],"name":event["name"],"dates":dates,
                         "venue":event["venue"],"official_url":event["official_url"],
                         "calendar_checked_at":event["checked_at"]})
    # Receipt dates are excluded from editorial facts: refreshing retrieval alone
    # must not create another draft. The week identifies a new weekly edition.
    facts = [{"id":"calendar","text":"大阪府内のゲーム・eスポーツの公式イベント予定を公開カレンダーで案内しています。","source_url":URL}]
    for event in upcoming:
        facts.append({"id":event["id"],"text":event["name"]+" / "+", ".join(event["dates"])+" / "+event["venue"],"source_url":event["official_url"]})
    return {"brand":"jesu_osaka","origin_brand":"jesu_osaka","kind":"news","url":URL+"?week="+monday.isoformat(),
            "title":"大阪のゲーム・eスポーツ予定｜"+monday.isoformat()+"週",
            "trigger":"news_published","visibility":"public","body_verified":True,
            "verified_at":now.isoformat(),"expires_at":expiry.isoformat(),
            "asset_policy":"official_public_only","facts":facts,
            "editorial_cycle":monday.isoformat(),
            "receipt":{"kind":"published_calendar_readback","url":URL,"observed_at":now.isoformat(),
                       "calendar_sha256":hashlib.sha256(calendar_block(live_html).encode()).hexdigest(),
                       "event_verification_dates":{e["id"]:e["calendar_checked_at"] for e in upcoming}},
            "editorial_instruction":"JeSU大阪のX @OsakaGamers専用。パックゼロ。今週の見どころを最大3件とカレンダーへのCTA1つ。外部催事をJeSU主催と書かない。個別告知へ展開する場合は当日公式URLを再確認。既存媒体別承認へ未チェックで提出。投稿・予約は本人承認後の既存配車係だけ。"}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--data",default=str(ROOT/"content/osaka-events.json"))
    p.add_argument("--inbox",default=str(Path.home()/".claude-local/x-loop/mascot-editorial/inbox"))
    p.add_argument("--pipeline",default=str(Path.home()/"pkg-ai-brain/claude/skills/mascot-sns-operations/scripts"))
    p.add_argument("--output",required=True)
    p.add_argument("--now")
    args=p.parse_args()
    now=dt.datetime.fromisoformat(args.now) if args.now else dt.datetime.now(JST)
    data=json.loads(Path(args.data).read_text())
    # Render from exactly the supplied data in memory; do not edit source HTML.
    spec=importlib.util.spec_from_file_location("events_renderer",ROOT/"scripts/render-events.py")
    renderer=importlib.util.module_from_spec(spec);spec.loader.exec_module(renderer)
    policy=json.loads((ROOT/"content/event-policy.json").read_text())
    renderer.validate(data,policy)
    rendered=START+"\n"+renderer.render(data,policy,"event-")+"\n"+END
    request=urllib.request.Request(URL,headers={"User-Agent":"JeSUOsaka-CalendarEditorial/1.0","Cache-Control":"no-cache"})
    with urllib.request.urlopen(request,timeout=30) as r:
        if r.geturl().split("?")[0] != URL: raise ValueError("unexpected public calendar redirect")
        live=r.read().decode("utf-8")
    item=source(data,rendered,live,now)
    sys.path.insert(0,args.pipeline)
    import campaign_pipeline as cp
    result=cp.enqueue(item,args.inbox)
    out=Path(args.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps({"source":item,"intake":result,"publication":"not_sent_approval_required"},ensure_ascii=False,indent=2)+"\n")
    print(json.dumps(result,ensure_ascii=False))
if __name__=="__main__":main()
