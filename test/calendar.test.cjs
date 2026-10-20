const { test } = require("node:test");
const assert = require("node:assert/strict");
const { statusLabel, occurrences, calendarMonths, upcomingIds } = require("../calendar.js");
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
