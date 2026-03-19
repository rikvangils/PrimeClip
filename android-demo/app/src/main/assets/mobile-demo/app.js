const demoClips = [
  {
    title: "Fit snack in 20 sec",
    platform: "TikTok",
    time: "19:30",
    status: "Ready",
    tags: ["Food", "UGC", "High CTR"],
    tint: "linear-gradient(150deg, #d8e8ff, #f4f9ff)",
  },
  {
    title: "Morning routine reset",
    platform: "TikTok",
    time: "20:00",
    status: "Draft",
    tags: ["Lifestyle", "Hook test"],
    tint: "linear-gradient(150deg, #e2f1ff, #f7fbff)",
  },
  {
    title: "3 sec product reveal",
    platform: "TikTok",
    time: "21:15",
    status: "Ready",
    tags: ["Product", "A/B 2 variants"],
    tint: "linear-gradient(150deg, #dbe9ff, #edf4ff)",
  },
  {
    title: "Street interview clip",
    platform: "TikTok",
    time: "22:00",
    status: "Needs review",
    tags: ["Voice over", "Trend pack"],
    tint: "linear-gradient(150deg, #e8f3ff, #f8fbff)",
  },
];

function renderClips() {
  const root = document.getElementById("clipList");
  root.innerHTML = "";

  for (const clip of demoClips) {
    const item = document.createElement("article");
    item.className = "clip-card";

    const thumb = document.createElement("div");
    thumb.className = "clip-thumb";
    thumb.style.background = clip.tint;

    const info = document.createElement("div");
    info.className = "clip-info";

    const title = document.createElement("h3");
    title.textContent = clip.title;

    const meta = document.createElement("p");
    meta.className = "clip-meta";
    meta.textContent = `${clip.platform} · ${clip.time}`;

    const chips = document.createElement("div");
    chips.className = "chips";

    const status = document.createElement("span");
    status.className = "chip" + (clip.status === "Ready" ? " success" : "");
    status.textContent = clip.status;
    chips.appendChild(status);

    for (const t of clip.tags) {
      const chip = document.createElement("span");
      chip.className = "chip";
      chip.textContent = t;
      chips.appendChild(chip);
    }

    info.appendChild(title);
    info.appendChild(meta);
    info.appendChild(chips);

    item.appendChild(thumb);
    item.appendChild(info);

    item.addEventListener("click", () => {
      document.getElementById("heroTitle").textContent = clip.title;
      document.getElementById("heroMeta").textContent = `${clip.platform} · ${clip.time} · ${clip.status}`;
      document.getElementById("heroPreview").style.background = clip.tint;
    });

    root.appendChild(item);
  }
}

function registerServiceWorker() {
  if (!("serviceWorker" in navigator)) {
    return;
  }
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("./sw.js").catch(() => {
      // Silent fail for simple demo.
    });
  });
}

renderClips();
registerServiceWorker();
