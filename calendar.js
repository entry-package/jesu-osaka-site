(() => {
  "use strict";
  const labels = {
    jesu: "JeSU関連",
    publisher: "ゲームメーカー",
    team: "プロチーム",
    creator: "配信者",
    public: "自治体・主要大会",
    package: "PACkage関連",
  };
  function statusLabel(event, today) {
    const label =
      event.status === "cancelled"
        ? "中止"
        : event.status === "postponed"
          ? "延期"
          : "開催予定";
    const stale =
      Date.parse(today + "T00:00:00Z") -
        Date.parse(event.checked_at + "T00:00:00Z") >
      8 * 86400000;
    return stale
      ? event.status === "scheduled"
        ? "要再確認"
        : label + "・要再確認"
      : label;
  }
  function occurrences(events, month, category, today) {
    return events
      .filter(
        (e) =>
          e.status !== "postponed" && (!category || e.category === category),
      )
      .flatMap((e) =>
        e.dates
          .filter((d) => d.startsWith(month) && d >= today)
          .map((d) => ({ date: d, event: e })),
      );
  }
  function calendarMonths(events, today) {
    const base = new Date(today.slice(0, 7) + "-01T00:00:00Z");
    const last = events.flatMap(e => e.dates).filter(d => d >= today).sort().at(-1);
    const end = last ? new Date(last.slice(0, 7) + "-01T00:00:00Z") : base;
    const count = Math.max(7, (end.getUTCFullYear() - base.getUTCFullYear()) * 12 + end.getUTCMonth() - base.getUTCMonth() + 1);
    return Array.from({length: count}, (_, i) => {
      const date = new Date(base); date.setUTCMonth(date.getUTCMonth() + i);
      return date.toISOString().slice(0, 7);
    });
  }
  function upcomingIds(events, month, category, today, scope) {
    return new Set(occurrences(events, scope === "all" ? "" : month, category, today).map(x => x.event.id));
  }
  if (typeof module !== "undefined")
    module.exports = { statusLabel, occurrences, calendarMonths, upcomingIds };
  if (typeof document === "undefined") return;
  const today = new Intl.DateTimeFormat("sv-SE", {
    timeZone: "Asia/Tokyo",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(new Date());
  document.querySelectorAll("[data-osaka-calendar]").forEach((root) => {
    const payload = JSON.parse(
      root.querySelector("[data-calendar-data]").textContent,
    );
    const monthSelect = root.querySelector("[data-calendar-month]");
    const categorySelect = root.querySelector("[data-calendar-category]");
    const items = [...root.querySelectorAll("[data-calendar-item]")];
    payload.events.forEach((e) => {
      const el = items.find((item) => item.dataset.calendarItem === e.id);
      if (el)
        el.querySelector(".local-event-meta > span:last-child").textContent =
          statusLabel(e, today);
    });
    const scopeSelect = root.querySelector("[data-calendar-scope]");
    const tabs = root.querySelector("[data-calendar-tabs]");
    const months = calendarMonths(payload.events, today);
    let month = months[0];
    monthSelect.replaceChildren(
      ...months.map((m) => {
        const o = document.createElement("option");
        o.value = m;
        o.textContent = m.replace("-", "年") + "月";
        return o;
      }),
    );
    monthSelect.value = month;
    root
      .querySelectorAll("[data-calendar-controls]")
      .forEach((el) => (el.hidden = false));
    const render = () => {
      month = monthSelect.value;
      const category = categorySelect.value;
      const dated = occurrences(payload.events, month, category, today);
      const visibleIds = upcomingIds(payload.events, month, category, today, scopeSelect.value);
      items.forEach(
        (el) => (el.hidden = !visibleIds.has(el.dataset.calendarItem)),
      );
      root.querySelector("[data-calendar-empty]").hidden = visibleIds.size > 0;
      const [year, m] = month.split("-").map(Number);
      const start = new Date(Date.UTC(year, m - 1, 1));
      const offset = (start.getUTCDay() + 6) % 7;
      const days = new Date(Date.UTC(year, m, 0)).getUTCDate();
      const body = root.querySelector("[data-calendar-body]");
      body.replaceChildren();
      for (let n = 0; n < Math.ceil((offset + days) / 7) * 7; n += 7) {
        const row = document.createElement("tr");
        for (let j = 0; j < 7; j++) {
          const cell = document.createElement("td");
          const day = n + j - offset + 1;
          if (day > 0 && day <= days) {
            const date = month + "-" + String(day).padStart(2, "0");
            const number = document.createElement("span");
            number.className = "calendar-day";
            number.textContent = day;
            if (date === today) {
              number.classList.add("is-today");
              number.setAttribute("aria-label", "今日 " + day + "日");
            }
            cell.append(number);
            dated
              .filter((x) => x.date === date)
              .forEach(({ event }) => {
                const a = document.createElement("a");
                a.href = "#" + (event.detail_anchor || root.dataset.calendarPrefix + event.id);
                a.className = "calendar-marker";
                a.setAttribute(
                  "aria-label",
                  date +
                    " " +
                    event.name +
                    (event.status === "cancelled" ? " 中止" : ""),
                );
                const dot = document.createElement("span");
                dot.textContent = event.status === "cancelled" ? "×" : "●";
                dot.setAttribute("aria-hidden", "true");
                const text = document.createElement("span");
                text.className = "calendar-marker-label";
                text.textContent =
                  event.status === "cancelled"
                    ? "中止"
                    : labels[event.category];
                a.append(dot, text);
                cell.append(a);
              });
          } else cell.className = "calendar-blank";
          row.append(cell);
        }
        body.append(row);
      }
      root.querySelector("[data-calendar-caption]").textContent =
        year + "年" + m + "月 府内のイベント予定";
      root.querySelector("[data-calendar-count]").textContent =
        (scopeSelect.value === "all" ? "これからの予定（全月） " : year + "年" + m + "月 ") + visibleIds.size + "件";
      tabs.replaceChildren(...months.map(value => {
        const button = document.createElement("button");
        button.type = "button";
        const count = upcomingIds(payload.events, value, category, today, "month").size;
        button.textContent = value.replace("-", "年") + "月（" + count + "件）";
        button.setAttribute("aria-pressed", String(value === month));
        button.addEventListener("click", () => {
          monthSelect.value = value;
          scopeSelect.value = "month";
          render(); wrapped();
        });
        return button;
      }));
    };
    monthSelect.addEventListener("change", () => {scopeSelect.value = "month"; render();});
    scopeSelect.addEventListener("change", render);
    categorySelect.addEventListener("change", render);
    root.querySelector("[data-calendar-prev]").addEventListener("click", () => {
      monthSelect.selectedIndex = Math.max(0, monthSelect.selectedIndex - 1);
      scopeSelect.value = "month";
      render();
    });
    root.querySelector("[data-calendar-next]").addEventListener("click", () => {
      monthSelect.selectedIndex = Math.min(
        months.length - 1,
        monthSelect.selectedIndex + 1,
      );
      scopeSelect.value = "month";
      render();
    });
    const wrapped = () => {
      root.querySelector("[data-calendar-prev]").disabled =
        monthSelect.selectedIndex === 0;
      root.querySelector("[data-calendar-next]").disabled =
        monthSelect.selectedIndex === months.length - 1;
    };
    monthSelect.addEventListener("change", wrapped);
    root
      .querySelector("[data-calendar-prev]")
      .addEventListener("click", wrapped);
    root
      .querySelector("[data-calendar-next]")
      .addEventListener("click", wrapped);
    render();
    wrapped();
  });
})();
