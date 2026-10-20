(() => {
  "use strict";
  const labels = {
    jesu: "JeSU関連",
    publisher: "ゲームメーカー",
    team: "プロチーム",
    creator: "配信者",
    public: "自治体・主要大会",
  };
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
    const factToday = Date.parse(today + "T00:00:00Z");
    payload.events.forEach((e) => {
      const el = items.find((item) => item.dataset.calendarItem === e.id);
      if (
        el &&
        factToday - Date.parse(e.checked_at + "T00:00:00Z") > 8 * 86400000
      )
        el.querySelector(".local-event-meta > span:last-child").textContent =
          "要再確認";
    });
    const first = payload.events
      .flatMap((e) => e.dates)
      .filter((d) => d >= today)
      .sort()[0];
    let month = (first || today).slice(0, 7);
    const months = [];
    const base = new Date(today.slice(0, 7) + "-01T00:00:00Z");
    for (let i = 0; i < 7; i++) {
      const d = new Date(base);
      d.setUTCMonth(d.getUTCMonth() + i);
      months.push(d.toISOString().slice(0, 7));
    }
    if (!months.includes(month)) month = months[0];
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
      const matches = payload.events.filter(
        (e) => !category || e.category === category,
      );
      const dated = matches.flatMap((e) =>
        e.dates
          .filter((d) => d.startsWith(month) && d >= today)
          .map((d) => ({ date: d, event: e })),
      );
      const visibleIds = new Set(dated.map((x) => x.event.id));
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
                a.href = "#" + root.dataset.calendarPrefix + event.id;
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
        visibleIds.size + "件のイベント";
    };
    monthSelect.addEventListener("change", render);
    categorySelect.addEventListener("change", render);
    root.querySelector("[data-calendar-prev]").addEventListener("click", () => {
      monthSelect.selectedIndex = Math.max(0, monthSelect.selectedIndex - 1);
      render();
    });
    root.querySelector("[data-calendar-next]").addEventListener("click", () => {
      monthSelect.selectedIndex = Math.min(
        months.length - 1,
        monthSelect.selectedIndex + 1,
      );
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
