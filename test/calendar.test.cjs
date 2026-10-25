const { test } = require("node:test");
const assert = require("node:assert/strict");
const { statusLabel, occurrences, calendarMonths, upcomingIds, todayInJapan, jesuInvolved } = require("../calendar.js");
const example = {
  id: "x",
  status: "scheduled",
  category: "publisher",
  checked_at: "2026-10-20",
  dates: ["2026-11-07", "2026-11-08"],
};
test("after eight days without confirmation event asks for recheck", () => {
  assert.equal(statusLabel(example, "2026-10-28"), "開催予定");
  assert.equal(statusLabel(example, "2026-10-29"), "要再確認");
});
test("staleness cannot erase cancellation", () => {
  assert.equal(
    statusLabel({ ...example, status: "cancelled" }, "2026-10-29"),
    "中止・要再確認",
  );
});
test("only actual future dates appear, never intervening days", () => {
  assert.deepEqual(
    occurrences([example], "2026-11", "", "2026-11-08").map((x) => x.date),
    ["2026-11-08"],
  );
});
test("category filters and past months return empty", () => {
  assert.equal(
    occurrences([example], "2026-11", "creator", "2026-10-20").length,
    0,
  );
  assert.equal(occurrences([example], "2026-10", "", "2026-10-20").length, 0);
});
test("unknown postponement is absent and cancellation remains visible", () => {
  assert.equal(
    occurrences(
      [{ ...example, status: "postponed" }],
      "2026-11",
      "",
      "2026-10-20",
    ).length,
    0,
  );
  assert.equal(
    occurrences(
      [{ ...example, status: "cancelled" }],
      "2026-11",
      "",
      "2026-10-20",
    ).length,
    2,
  );
});

test("calendar starts in current month even when first event is next month", () => {
  assert.equal(calendarMonths([example], "2026-10-21")[0], "2026-10");
});
test("month range crosses years and retains distant published dates", () => {
  const months = calendarMonths([{...example, dates:["2028-01-01"]}], "2026-10-21");
  assert.ok(months.includes("2026-12"));
  assert.ok(months.includes("2027-01"));
  assert.equal(months.at(-1), "2028-01");
});
test("all-month listing retains December and next year while month scope filters", () => {
  const events = [example, {...example,id:"dec",dates:["2026-12-26","2026-12-27"]}, {...example,id:"mar",dates:["2027-03-13"]}];
  assert.deepEqual([...upcomingIds(events,"2026-10","","2026-10-21","all")], ["x","dec","mar"]);
  assert.deepEqual([...upcomingIds(events,"2026-12","","2026-10-21","month")], ["dec"]);
  assert.equal(upcomingIds(events,"2026-10","team","2026-10-21","all").size,0);
});

const involved = {...example, category:"jesu", organizer:"JeSU大阪"};
test("default upcoming list includes today and keeps only the two closest events", () => {
  const events = [
    {...involved, id:"next-month", dates:["2026-11-01"]},
    {...involved, id:"past", dates:["2026-10-24"]},
    {...involved, id:"late-today", dates:["2026-10-25"], start_time:"18:00"},
    {...involved, id:"early-today", dates:["2026-10-25"], start_time:"09:00"},
  ];
  assert.deepEqual([...upcomingIds(events,"2026-10","","2026-10-25","upcoming")], ["early-today","late-today"]);
  assert.deepEqual([...upcomingIds(events,"2026-10","","2026-10-26","upcoming")], ["next-month"]);
});
test("multi-day events count once and are ordered by their next actual date", () => {
  const events = [
    {...involved, id:"multi", dates:["2026-10-24","2026-10-27","2026-10-28"]},
    {...involved, id:"today", dates:["2026-10-25"]},
    {...involved, id:"tomorrow", dates:["2026-10-26"]},
  ];
  assert.deepEqual([...upcomingIds(events,"2026-10","","2026-10-25","upcoming")], ["today","tomorrow"]);
  assert.deepEqual([...upcomingIds(events,"2026-10","","2026-10-27","upcoming")], ["multi"]);
});
test("initial two exclude cancelled and postponed events without hiding calendar notices", () => {
  const events = [
    {...involved,id:"cancelled",status:"cancelled",dates:["2026-10-25"]},
    {...involved,id:"postponed",status:"postponed",dates:["2026-10-25"]},
    {...involved,id:"next",dates:["2026-11-01"]},
  ];
  assert.deepEqual([...upcomingIds(events,"2026-10","","2026-10-25","upcoming")], ["next"]);
  assert.deepEqual([...upcomingIds(events,"2026-10","","2026-10-25","all")], ["cancelled","next"]);
});
test("upcoming filter stays empty when nothing remains and preserves category selection", () => {
  assert.equal(upcomingIds([involved],"2026-11","creator","2026-11-07","upcoming").size,0);
  assert.equal(upcomingIds([involved],"2026-11","","2026-11-09","upcoming").size,0);
});
test("visitor day follows Japan midnight regardless of host timezone", () => {
  assert.equal(todayInJapan(new Date("2026-10-25T14:59:59Z")),"2026-10-25");
  assert.equal(todayInJapan(new Date("2026-10-25T15:00:00Z")),"2026-10-26");
});

test("upcoming means JeSU involvement, not category or PACkage association alone", () => {
  const events = [
    {...example, id:"external", dates:["2026-10-25"]},
    {...example, id:"package", dates:["2026-10-25"], category:"corporate", organizer:"株式会社PACkage", package_relation:{role:"主催"}},
    {...example, id:"label-only", dates:["2026-10-25"], category:"jesu", organizer:"外部主催者"},
    {...involved, id:"hosted", dates:["2026-10-26"]},
    {...example, id:"supported", dates:["2026-10-27"], jesu_role:"後援"},
    {...involved, id:"later", dates:["2026-10-28"]},
  ];
  assert.deepEqual([...upcomingIds(events,"2026-10","","2026-10-25","upcoming")], ["hosted","supported"]);
  assert.equal(upcomingIds(events,"2026-10","","2026-10-25","all").size,6);
  assert.deepEqual([...upcomingIds(events.slice(0,4),"2026-10","","2026-10-25","upcoming")], ["hosted"]);
  assert.equal(upcomingIds(events.slice(0,3),"2026-10","","2026-10-25","upcoming").size,0);
});
test("JeSU national and branch organizers and supported roles are accepted", () => {
  assert.equal(jesuInvolved({...involved, organizer:"一般社団法人日本eスポーツ連合"}),true);
  for(const jesu_role of ["主催","共催","運営","後援","協力"])
    assert.equal(jesuInvolved({...example,jesu_role}),true);
  assert.equal(jesuInvolved({...example,jesu_role:"来場"}),false);
});
