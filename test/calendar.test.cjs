const { test } = require("node:test");
const assert = require("node:assert/strict");
const { statusLabel, occurrences } = require("../calendar.js");
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
