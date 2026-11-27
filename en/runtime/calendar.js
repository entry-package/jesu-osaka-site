(() => {
  "use strict";
  const formatMonth = value => new Intl.DateTimeFormat("en", {
    month: "long", year: "numeric", timeZone: "UTC",
  }).format(new Date(value + "-01T00:00:00Z"));
  const labels = {
    jesu: "JeSU-related",
    publisher: "Game publishers",
    team: "Pro teams",
    creator: "Streamers",
    public: "Local government and major tournaments",
    corporate: "Company-organized",
  };
  function statusLabel(event, today) {
    if (event.show_completed_in_month && event.status === "scheduled") {
      if (event.dates.at(-1) < today) return "Ended";
      if (event.dates.includes(today)) return "In progress";
    }
    const label =
      event.status === "cancelled"
        ? "Cancelled"
        : event.status === "postponed"
          ? "Postponed"
          : "Upcoming";
    const stale =
      Date.parse(today + "T00:00:00Z") -
        Date.parse(event.checked_at + "T00:00:00Z") >
      8 * 86400000;
    return stale
      ? event.status === "scheduled"
        ? "Check for updates"
        : label + " · Check for updates"
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
          .filter((d) => d.startsWith(month) && (d >= today || (month && e.show_completed_in_month)))
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
  function jesuInvolved(event) {
    if (["主催", "共催", "運営", "後援", "協力"].includes(event.jesu_role)) return true;
    const organizer = event.source_organizer || event.organizer || "";
    return event.category === "jesu" &&
      (organizer.includes("JeSU") || organizer.includes("eスポーツ連合"));
  }
  function upcomingIds(events, month, category, today, scope) {
    const dated = occurrences(events, scope === "month" ? month : "", category, today)
      .filter(({ event }) => scope !== "upcoming" || (event.status === "scheduled" && jesuInvolved(event)))
      .sort((a, b) => a.date.localeCompare(b.date) ||
        (a.event.start_time || "00:00").localeCompare(b.event.start_time || "00:00"));
    const ids = [...new Set(dated.map(x => x.event.id))];
    return new Set(scope === "upcoming" ? ids.slice(0, 2) : ids);
  }
  function todayInJapan(now = new Date()) {
    return new Intl.DateTimeFormat("sv-SE", {
      timeZone: "Asia/Tokyo", year: "numeric", month: "2-digit", day: "2-digit",
    }).format(now);
  }
  if (typeof module !== "undefined")
    module.exports = { statusLabel, occurrences, calendarMonths, upcomingIds, todayInJapan, jesuInvolved };
  if (typeof document === "undefined") return;
  // The weekly publisher changes the Japanese calendar blocks only. Read their
  // verified facts from the same Pages site and retain the reviewed English copy
  // where its Japanese source has not changed.
  const publishedSite = typeof document === "undefined" ? null
    : new URL("../../", document.currentScript.src);
  const sourceFields = {
    name: "source_name", organizer: "source_organizer", calendar_label: "source_calendar_label",
    summary: "source_summary", organizer_label: "source_organizer_label",
  };
  const calendarDate = /^\d{4}-\d{2}-\d{2}$/;
  const dateFormatter = new Intl.DateTimeFormat("en", {
    month: "short", day: "numeric", weekday: "short", timeZone: "UTC",
  });
  const compareValue = (a, b) => JSON.stringify(a) === JSON.stringify(b);
  function localizeFacts(event, reviewed) {
    const localized = {...event, source_organizer: event.organizer};
    for (const [field, source] of Object.entries(sourceFields)) {
      if (reviewed?.[source] === event[field] && reviewed?.[field] !== undefined) {
        localized[field] = reviewed[field];
      } else if (field === "calendar_label") {
        delete localized[field];
      }
    }
    return localized;
  }
  function setText(node, value, japanese = false) {
    node.textContent = value;
    if (japanese && /[\u3040-\u30ff\u3400-\u9fff]/u.test(value)) node.lang = "ja";
    return node;
  }
  function makeCard(prefix, event, oldEvent, oldCard) {
    const card = document.createElement("article");
    card.className = "local-event";
    card.dataset.calendarItem = event.id;
    const localized = localizeFacts(event, oldEvent);
    const child = (tag, parent, text = "", className = "", japanese = false) => {
      const node = setText(document.createElement(tag), text, japanese);
      node.className = className;
      parent.append(node);
      return node;
    };
    const anchor = event.detail_anchor && document.getElementById(event.detail_anchor);
    if (anchor) card.classList.add("local-event-reference");
    else card.id = prefix + event.id;
    const meta = child("div", card, "", "local-event-meta");
    child("span", meta, anchor ? oldCard?.querySelector(".tag")?.textContent || "JeSU Osaka-organized"
      : labels[event.category], "tag neutral");
    child("span", meta);
    const dates = event.dates.map(date => dateFormatter.format(new Date(date + "T00:00:00Z")));
    const date = child("p", card, dates.join(" · "), "local-event-date");
    const times = event.start_time ? event.start_time + (event.end_time ? "–" + event.end_time : "")
      : "Start time not announced";
    child("span", date, times);
    child("h3", card, localized.name, "", localized.name === event.name);
    if (anchor) {
      const link = child("a", card, "View the event details above ↑", "text-link");
      link.href = "#" + event.detail_anchor;
      return card;
    }
    const summary = oldCard?.querySelector(":scope > p:not(.local-event-date)")?.textContent;
    const oldDetails = [...(oldCard?.querySelectorAll("dd") || [])];
    const keep = (key, value, oldText) => {
      const reviewed = oldEvent && oldText && compareValue(event[key], oldEvent[sourceFields[key] || key])
        && (key !== "venue" || event.city === oldEvent.city);
      return reviewed ? [oldText, false] : [value, true];
    };
    const [summaryText, summaryJa] = keep("summary", event.summary, summary);
    child("p", card, summaryText, "", summaryJa);
    const facts = child("dl", card);
    for (const [label, [value, japanese]] of [
      ["Venue", keep("venue", event.venue + " (" + event.city + ")", oldDetails[0]?.textContent)],
      [event.organizer_label === "情報提供" ? "Information provided by" : "Organizer",
        [localized.organizer, localized.organizer === event.organizer]],
      ["Entry", keep("fee", event.fee, oldDetails[2]?.textContent)],
    ]) {
      const row = child("div", facts);
      child("dt", row, label);
      child("dd", row, value, "", japanese);
    }
    const footer = child("div", card, "", "local-event-footer");
    const official = child("a", footer, "Check the official event website ↗", "text-link");
    official.href = event.official_url;
    official.target = "_blank";
    official.rel = "noopener";
    child("small", footer, "Verified " + event.checked_at.replaceAll("-", "."));
    return card;
  }
  function isPublishedEvent(event) {
    return /^[a-z0-9-]+$/.test(event?.id) && Object.hasOwn(labels, event.category)
      && ["scheduled", "cancelled", "postponed"].includes(event.status)
      && (!event.detail_anchor || /^[a-z0-9-]+$/.test(event.detail_anchor))
      && Array.isArray(event.dates) && event.dates.length > 0
      && event.dates.every(date => typeof date === "string" && calendarDate.test(date)
          && !Number.isNaN(Date.parse(date)))
      && [event.name, event.organizer, event.summary, event.venue, event.city, event.fee]
          .every(value => typeof value === "string")
      && typeof event.checked_at === "string" && calendarDate.test(event.checked_at)
      && typeof event.official_url === "string" && URL.canParse(event.official_url)
      && new URL(event.official_url).protocol === "https:";
  }
  document.querySelectorAll("[data-osaka-calendar]").forEach((root) => {
    let today = todayInJapan();
    const payload = JSON.parse(
      root.querySelector("[data-calendar-data]").textContent,
    );
    const monthSelect = root.querySelector("[data-calendar-month]");
    const categorySelect = root.querySelector("[data-calendar-category]");
    let items = [...root.querySelectorAll("[data-calendar-item]")];
    const scopeSelect = root.querySelector("[data-calendar-scope]");
    const tabs = root.querySelector("[data-calendar-tabs]");
    let months;
    let month;
    const reviewedEvents = new Map(payload.events.map(event => [event.id, event]));
    const reviewedCards = new Map(items.map(card => [card.dataset.calendarItem, card]));
    const reviewLabel = root.querySelector(".calendar-updated");
    let lastPublishedFacts;
    const refreshPublishedCalendar = async () => {
      if (!["http:", "https:"].includes(publishedSite.protocol)) return;
      const prefix = root.dataset.calendarPrefix;
      const source = new URL(prefix === "home-" ? "./" : "events.html", publishedSite);
      const response = await fetch(source, {cache: "no-cache", mode: "same-origin"});
      if (!response.ok || new URL(response.url).origin !== publishedSite.origin) return;
      const page = new DOMParser().parseFromString(await response.text(), "text/html");
      const snapshot = page.querySelector(`[data-osaka-calendar][data-calendar-prefix="${prefix}"]`);
      const checked = snapshot?.querySelector(".calendar-updated")?.textContent
        .match(/\b\d{4}\.\d{2}\.\d{2}\b/)?.[0];
      const raw = snapshot?.querySelector("[data-calendar-data]")?.textContent;
      if (!checked || !raw || page.documentElement.lang !== "ja") return;
      const facts = checked + raw;
      if (facts === lastPublishedFacts) return;
      const {events} = JSON.parse(raw);
      if (!Array.isArray(events) || !events.every(isPublishedEvent)
          || new Set(events.map(event => event.id)).size !== events.length) return;
      const original = event => {
        const reviewed = reviewedEvents.get(event.id);
        return reviewed && Object.entries(event).every(([key, value]) =>
          compareValue(value, reviewed[sourceFields[key] || key]))
          && Object.keys(reviewed).every(key => (Object.values(sourceFields).includes(key) || Object.hasOwn(event, key)));
      };
      const cards = events.filter(original).length;
      if (lastPublishedFacts || cards !== events.length || reviewedEvents.size !== events.length
          || !reviewLabel.textContent.includes(checked)) {
        const next = events.map(event => original(event) ? reviewedCards.get(event.id).cloneNode(true)
          : makeCard(prefix, event, reviewedEvents.get(event.id), reviewedCards.get(event.id)));
        const empty = root.querySelector("[data-calendar-empty]");
        for (const card of items) card.remove();
        empty.before(...next);
        items = next;
        payload.events = events.map(event => localizeFacts(event, reviewedEvents.get(event.id)));
        if (!reviewLabel.textContent.includes(checked)) {
          reviewLabel.textContent = "Japanese calendar last checked: " + checked;
        }
        updateMonths();
        render();
        wrapped();
        revealLinkedEvent();
      }
      lastPublishedFacts = facts;
    };
    const syncCalendar = () => refreshPublishedCalendar().catch(() => {});
    const updateMonths = () => {
      const selected = monthSelect.value;
      months = calendarMonths(payload.events, today);
      monthSelect.replaceChildren(...months.map((m) => {
        const option = document.createElement("option");
        option.value = m;
        option.textContent = formatMonth(m);
        return option;
      }));
      month = months.includes(selected) ? selected : months[0];
      monthSelect.value = month;
    };
    updateMonths();
    root
      .querySelectorAll("[data-calendar-controls]")
      .forEach((el) => (el.hidden = false));
    const render = () => {
      const currentDay = todayInJapan();
      if (currentDay !== today) {
        today = currentDay;
        updateMonths();
      }
      payload.events.forEach((event) => {
        const el = items.find(item => item.dataset.calendarItem === event.id);
        if (el) el.querySelector(".local-event-meta > span:last-child").textContent =
          statusLabel(event, today);
      });
      month = monthSelect.value;
      const category = categorySelect.value;
      const dated = occurrences(payload.events, month, category, today);
      const visibleIds = upcomingIds(payload.events, month, category, today, scopeSelect.value);
      items.forEach(
        (el) => (el.hidden = !visibleIds.has(el.dataset.calendarItem)),
      );
      const empty = root.querySelector("[data-calendar-empty]");
      for (const id of visibleIds) {
        const el = items.find(item => item.dataset.calendarItem === id);
        if (el) empty.before(el);
      }
      empty.hidden = visibleIds.size > 0;
      empty.textContent = scopeSelect.value === "upcoming"
        ? "No upcoming JeSU-related events match. Select Upcoming events (all months) for listings across Osaka."
        : "No events match these filters. Try another month or category.";
      const [year, m] = month.split("-").map(Number);
      const start = new Date(Date.UTC(year, m - 1, 1));
      const offset = start.getUTCDay();
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
              number.setAttribute("aria-label", "Today, day " + day);
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
                    (event.status === "cancelled" ? " — cancelled" : ""),
                );
                const dot = document.createElement("span");
                dot.textContent = event.status === "cancelled" ? "×" : "●";
                dot.setAttribute("aria-hidden", "true");
                const text = document.createElement("span");
                text.className = "calendar-marker-label";
                text.textContent =
                  event.status === "cancelled"
                    ? "Cancelled"
                    : (event.calendar_label || labels[event.category]);
                a.append(dot, text);
                a.addEventListener("click", () => {
                  const target = document.getElementById(a.hash.slice(1));
                  if (target && target.matches("[data-calendar-item][hidden]")) {
                    scopeSelect.value = "month";
                    render();
                    wrapped();
                  }
                });
                cell.append(a);
              });
          } else cell.className = "calendar-blank";
          row.append(cell);
        }
        body.append(row);
      }
      root.querySelector("[data-calendar-caption]").textContent =
        formatMonth(monthSelect.value) + " events in Osaka Prefecture";
      root.querySelector("[data-calendar-count]").textContent =
        (scopeSelect.value === "upcoming" ? "JeSU-related events (including today): " :
          scopeSelect.value === "all" ? "Upcoming events (all months): " : formatMonth(monthSelect.value) + ": ") +
          visibleIds.size;
      tabs.replaceChildren(...months.map(value => {
        const button = document.createElement("button");
        button.type = "button";
        const count = upcomingIds(payload.events, value, category, today, "month").size;
        button.textContent = formatMonth(value) + " (" + count + ")";
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
    const revealLinkedEvent = () => {
      const target = items.find(item => item.id === location.hash.slice(1));
      if (target && target.hidden &&
          upcomingIds(payload.events, "", categorySelect.value, today, "all").has(target.dataset.calendarItem)) {
        scopeSelect.value = "all";
        render();
        target.scrollIntoView();
      }
    };
    const refreshDay = () => {
      if (todayInJapan() !== today) {
        render();
        wrapped();
      }
    };
    window.addEventListener("hashchange", revealLinkedEvent);
    window.addEventListener("pageshow", refreshDay);
    window.addEventListener("pageshow", syncCalendar);
    document.addEventListener("visibilitychange", refreshDay);
    window.setInterval(refreshDay, 60_000);
    render();
    wrapped();
    revealLinkedEvent();
  });
})();
