#!/usr/bin/env python3
"""Validate official event facts and render progressive-enhancement calendar blocks."""
import argparse,calendar,datetime as dt,html,json,re
from pathlib import Path
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parents[1]
def escape(s):return html.escape(str(s),quote=True)
def validate(data,policy):
 errors=[];seen=set();slots=set()
 for e in data["events"]:
  if e["id"] in seen:errors.append("duplicate id "+e["id"])
  seen.add(e["id"])
  for k in ("id","name","organizer","city","venue","official_url","checked_at","source_owner"):
   if not e.get(k):errors.append(e.get("id","?")+": missing "+k)
  if not re.fullmatch(r"[a-z0-9-]+",e["id"]):errors.append("unsafe id")
  if e.get("prefecture")!="大阪府" or e.get("format")!="offline":errors.append(e["id"]+": outside Osaka / online only")
  if e.get("category") not in policy["categories"]:errors.append("unknown category")
  if e.get("status") not in ("scheduled","cancelled","postponed"):errors.append("unknown status")
  if e.get("importance",{}).get("kind") not in policy["importance_kinds"]:errors.append("missing major-event basis")
  for key in ("official_url","source_url"):
   u=urlsplit(e.get(key,""));host=u.hostname or ""
   if u.scheme!="https" or u.username or u.password or not any(host==h or host.endswith("."+h) for h in policy["source_hosts"]):errors.append(e["id"]+": unverified official host "+key)
  u=urlsplit(e.get("importance",{}).get("evidence_url",""))
  if u.scheme!="https" or not u.hostname:errors.append("missing importance evidence")
  if e.get("importance",{}).get("kind")=="team_creator_major" and e.get("capacity",0)<policy["major_capacity_threshold"]:errors.append("large team/creator event capacity unconfirmed")
  checked=dt.date.fromisoformat(e["checked_at"])
  if checked>dt.date.fromisoformat(data["last_checked"]):errors.append("future verification date")
  if not e.get("dates") or e["dates"]!=sorted(set(e["dates"])):errors.append("dates missing or duplicated")
  for d in e["dates"]:
   dt.date.fromisoformat(d);slot=(e.get("series_id",e["id"]),d,e["venue"])
   if slot in slots:errors.append("duplicate event/date/venue")
   slots.add(slot)
  for key in ("start_time","end_time"):
   if e.get(key):dt.time.fromisoformat(e[key])
 if errors:raise ValueError("; ".join(errors))
 return data
def date_label(d):
 x=dt.date.fromisoformat(d);return f'{x.month}/{x.day}（{"月火水木金土日"[x.weekday()]}）'
def active_events(data,policy):
 today=dt.date.fromisoformat(data["last_checked"]);last=today+dt.timedelta(days=policy["lookahead_days"])
 return sorted([e for e in data["events"] if e["status"]!="postponed" and any(today<=dt.date.fromisoformat(d)<=last for d in e["dates"])],key=lambda e:next(d for d in e["dates"] if dt.date.fromisoformat(d)>=today))
def render(data,policy,prefix):
 events=active_events(data,policy);labels=policy["categories"]
 first=events[0]["dates"][0] if events else data["last_checked"];year,month=map(int,first[:7].split("-"))
 byday={}
 for e in events:
  for d in e["dates"]:byday.setdefault(d,[]).append(e)
 rows=[]
 for week in calendar.Calendar(0).monthdayscalendar(year,month):
  cells=[]
  for day in week:
   if not day:cells.append('<td class="calendar-blank"></td>');continue
   d=f"{year}-{month:02d}-{day:02d}"
   links=''.join(f'<a class="calendar-marker" href="#{prefix}{e["id"]}" aria-label="{d} {escape(e["name"])}"><span aria-hidden="true">{"×" if e["status"]=="cancelled" else "●"}</span><span class="calendar-marker-label">{labels[e["category"]]}</span></a>' for e in byday.get(d,[]))
   cells.append(f'<td><span class="calendar-day">{day}</span>{links}</td>')
  rows.append('<tr>'+''.join(cells)+'</tr>')
 cards=[]
 for e in events:
  dates='・'.join(date_label(d) for d in e["dates"])
  status="中止" if e["status"]=="cancelled" else "開催予定"
  times=(e.get("start_time") or "開始時刻未公表")+("–"+e["end_time"] if e.get("end_time") else "")
  stale=(dt.date.fromisoformat(data["last_checked"])-dt.date.fromisoformat(e["checked_at"])).days>policy["stale_after_days"]
  cards.append(f'''<article class="local-event" id="{prefix}{e["id"]}" data-calendar-item="{e["id"]}">
  <div class="local-event-meta"><span class="tag neutral">{labels[e["category"]]}</span><span>{"要再確認" if stale else status}</span></div>
  <p class="local-event-date">{dates}<span>{times}</span></p><h3>{escape(e["name"])}</h3>
  <p>{escape(e["summary"])}</p><dl><div><dt>会場</dt><dd>{escape(e["venue"])}（{escape(e["city"])}）</dd></div>
  <div><dt>主催</dt><dd>{escape(e["organizer"])}</dd></div><div><dt>参加</dt><dd>{escape(e["fee"])}</dd></div></dl>
  <div class="local-event-footer"><a class="text-link" href="{escape(e["official_url"])}" target="_blank" rel="noopener">公式サイトで確認 ↗</a><small>情報確認 {e["checked_at"].replace("-",".")}</small></div></article>''')
 payload=json.dumps({"events":events},ensure_ascii=False).replace("</","<\\/")
 options=''.join(f'<option value="{k}">{v}</option>' for k,v in labels.items())
 return f'''<section class="osaka-calendar" id="osaka-events" data-osaka-calendar data-calendar-prefix="{prefix}">
 <div class="section-heading"><div><p class="eyebrow">OSAKA EVENT CALENDAR</p><h2>府内のイベント予定</h2></div><a class="text-link" href="./event-guidelines.html">掲載基準 ↗</a></div>
 <p class="calendar-intro">大阪で出会える、ゲームとeスポーツの大きな舞台。<br>JeSU関連、ゲームメーカー、プロチーム・配信者などの公式発表からご紹介します。</p>
 <p class="calendar-note">外部イベントは各主催者による開催です。最新の日程・参加条件は公式サイトをご確認ください。</p>
 <div class="calendar-toolbar" data-calendar-controls hidden><div class="calendar-month-control"><button type="button" data-calendar-prev aria-label="前の月">←</button><label>表示月<select data-calendar-month aria-label="表示する月"></select></label><button type="button" data-calendar-next aria-label="次の月">→</button></div>
 <label class="calendar-category">種別<select data-calendar-category aria-label="イベントの種別"><option value="">すべて</option>{options}</select></label></div>
 <div class="calendar-layout"><div class="calendar-table-wrap"><table class="calendar-table"><caption data-calendar-caption>{year}年{month}月 府内のイベント予定</caption><thead><tr>{''.join('<th scope="col">'+x+'</th>' for x in '月火水木金土日')}</tr></thead><tbody data-calendar-body>{''.join(rows)}</tbody></table><p class="calendar-legend">● 開催予定　× 中止　日付の印から詳細へ</p><p class="calendar-updated">情報確認：{data["last_checked"].replace("-",".")} ／ 毎週更新</p></div>
 <div class="local-event-list"><p class="calendar-count" data-calendar-count role="status">{len(events)}件のイベント</p>{''.join(cards)}<p class="calendar-empty" data-calendar-empty hidden>この月・種別の掲載予定はありません。ほかの月・種別もご覧ください。</p></div></div>
 <noscript><p>JavaScriptが無効な場合は、上記カレンダーと日程順の一覧をご利用ください。</p></noscript>
 <script type="application/json" data-calendar-data>{payload}</script></section>'''
def main():
 p=argparse.ArgumentParser();p.add_argument("--check",action="store_true");a=p.parse_args()
 data=json.loads((ROOT/"content/osaka-events.json").read_text());policy=json.loads((ROOT/"content/event-policy.json").read_text());validate(data,policy)
 if a.check:print(json.dumps({"events":len(data["events"]),"valid":True}));return
 for name,prefix in [("index.html","home-"),("events.html","event-")]:
  path=ROOT/name;s=path.read_text();block="<!-- OSAKA_CALENDAR_START -->\n"+render(data,policy,prefix)+"\n<!-- OSAKA_CALENDAR_END -->"
  pattern=r"<!-- OSAKA_CALENDAR_START -->.*?<!-- OSAKA_CALENDAR_END -->"
  if re.search(pattern,s,re.S):s=re.sub(pattern,lambda m:block,s,flags=re.S)
  elif name=="index.html":
   at=s.index('          <div class="event-intake">');s=s[:at]+block+"\n"+s[at:];s=s.replace("学ぶ。出会う。楽しむ。","JeSU大阪の開催予定")
  else:
   at=s.index('      <section class="section past-events">');s=s[:at]+'<div class="section">'+block+'</div>\n'+s[at:];s=s.replace("<h2>開催予定</h2>","<h2>JeSU大阪の開催予定</h2>")
  s=s.replace('<script src="./site.js" defer></script>','<script src="./site.js" defer></script>\n    <script src="./calendar.js" defer></script>') if 'src="./calendar.js"' not in s else s
  path.write_text(s)
 print(json.dumps({"rendered":2,"events":len(data["events"]),"checked":data["last_checked"]}))
if __name__=="__main__":main()
