(() => {
  "use strict";
  const menu = document.querySelector(".mobile-menu");
  if (menu) {
    menu.querySelectorAll("a").forEach((a) =>
      a.addEventListener("click", () => {
        menu.open = false;
      }),
    );
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && menu.open) {
        menu.open = false;
        menu.querySelector("summary").focus();
      }
    });
    document.addEventListener("click", (e) => {
      if (menu.open && !menu.contains(e.target)) menu.open = false;
    });
  }
  // Do not leave an ended event looking open for registration.
  document.querySelectorAll("[data-event-end]").forEach((card) => {
    if (Date.now() >= Date.parse(card.dataset.eventEnd)) {
      card.querySelector("[data-event-status]").textContent = "日程終了";
      card.querySelector("[data-event-link]").textContent =
        "開催案内を見る（Peatix） ↗";
      const heading = document.querySelector("#upcoming h2");
      if (heading) heading.textContent = "掲載イベント";
    }
  });
  // A review host must never send a real inquiry to the production receiver.
  const form = document.querySelector(".native-form");
  if (
    form &&
    !["www.jesu-osaka.jp", "jesu-osaka.jp"].includes(location.hostname)
  ) {
    const button = form.querySelector('[type="submit"]');
    button.textContent = "確認用：送信は停止しています";
    button.disabled = true;
    form.addEventListener(
      "submit",
      (e) => {
        e.preventDefault();
        e.stopImmediatePropagation();
      },
      true,
    );
  }
})();
