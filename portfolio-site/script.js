const mediaSections = [
  {
    title: "Dokumentation / finished installation",
    items: [
      {
        file: "panoramic-space-overview-fov-of-receivers.JPG",
        path: "Dokumentation/finished installation/panoramic-space-overview-fov-of-receivers.JPG",
        date: "2026-05-08",
      },
      {
        file: "final-backend-ui.png",
        path: "Dokumentation/finished installation/final-backend-ui.png",
        date: "2026-05-08",
      },
      {
        file: "finished-installation.JPG",
        path: "Dokumentation/finished installation/finished-installation.JPG",
        date: "2026-05-08",
      },
      {
        file: "inside-view-with-description.JPG",
        path: "Dokumentation/finished installation/inside-view-with-description.JPG",
        date: "2026-05-08",
      },
      {
        file: "installation-outside-view-with-visible-hardware-setup.JPG",
        path: "Dokumentation/finished installation/installation-outside-view-with-visible-hardware-setup.JPG",
        date: "2026-05-08",
      },
    ],
  },
  {
    title: "Dokumentation / Work in Progress / building the installation",
    items: [
      {
        file: "first-receiver-test-setup.JPG",
        path: "Dokumentation/Work in Progress/building the installation/first-receiver-test-setup.JPG",
        date: "2026-05-05",
      },
      {
        file: "3-receiver-1-sender-setup-test.JPG",
        path: "Dokumentation/Work in Progress/building the installation/3-receiver-1-sender-setup-test.JPG",
        date: "2026-05-05",
      },
      {
        file: "abandoned-esp32-board-with-external-antenna.JPG",
        path: "Dokumentation/Work in Progress/building the installation/abandoned-esp32-board-with-external-antenna.JPG",
        date: "2026-05-06",
      },
      {
        file: "test-setup-through-wall.JPG",
        path: "Dokumentation/Work in Progress/building the installation/test-setup-through-wall.JPG",
        date: "2026-05-06",
      },
      {
        file: "space-overview.JPG",
        path: "Dokumentation/Work in Progress/building the installation/space-overview.JPG",
        date: "2026-05-06",
      },
      {
        file: "Through-wall-test-setup.JPG",
        path: "Dokumentation/Work in Progress/building the installation/Through-wall-test-setup.JPG",
        date: "2026-05-06",
      },
      {
        file: "receiver-fixture-prototypes.JPG",
        path: "Dokumentation/Work in Progress/building the installation/receiver-fixture-prototypes.JPG",
        date: "2026-05-07",
      },
      {
        file: "rssi-testing-setup-same-side.JPG",
        path: "Dokumentation/Work in Progress/building the installation/rssi-testing-setup-same-side.JPG",
        date: "2026-05-07",
      },
      {
        file: "rssi-calibration-setup.JPG",
        path: "Dokumentation/Work in Progress/building the installation/rssi-calibration-setup.JPG",
        date: "2026-05-07",
      },
      {
        file: "setting-up-for-installation.JPG",
        path: "Dokumentation/Work in Progress/building the installation/setting-up-for-installation.JPG",
        date: "2026-05-08",
      },
    ],
  },
];

function assetPath(path) {
  const prefix = window.location.pathname.includes("/portfolio-site/") ? "../" : "";
  return encodeURI(`${prefix}${path}`);
}

function projectDescriptionPath() {
  const prefix = window.location.pathname.includes("/portfolio-site/") ? "../" : "";
  return `${prefix}project-description.md`;
}

function findVimeoUrl(markdown) {
  const match = markdown.match(/https?:\/\/(?:www\.)?(?:player\.)?vimeo\.com\/[^\s)>\]]+/i);
  return match ? match[0] : "";
}

function vimeoEmbedUrl(url) {
  if (!url) return "";

  try {
    const parsed = new URL(url);

    if (parsed.hostname.includes("player.vimeo.com")) {
      return url;
    }

    const id = parsed.pathname
      .split("/")
      .filter(Boolean)
      .find((part) => /^\d+$/.test(part));

    if (id) {
      return `https://player.vimeo.com/video/${id}`;
    }
  } catch (_) {
    return "";
  }

  return "";
}

async function renderHeroVideo() {
  const target = document.querySelector("#hero-video");

  if (!target) return;

  let heroVimeoUrl = "";

  try {
    const response = await fetch(projectDescriptionPath());
    if (response.ok) {
      heroVimeoUrl = findVimeoUrl(await response.text());
    }
  } catch (_) {
    heroVimeoUrl = "";
  }

  const embed = vimeoEmbedUrl(heroVimeoUrl);

  if (embed) {
    const iframe = document.createElement("iframe");
    iframe.src = `${embed}?title=0&byline=0&portrait=0`;
    iframe.title = "Veiled Panopticon video";
    iframe.allow = "autoplay; fullscreen; picture-in-picture";
    iframe.allowFullscreen = true;
    target.append(iframe);
    return;
  }

  const placeholder = document.createElement("div");
  placeholder.className = "video-placeholder";
  placeholder.textContent = "Vimeo video URL missing from project-description.md";
  target.append(placeholder);
}

function renderMediaSections() {
  const container = document.querySelector("#media-sections");
  if (!container) return;

  mediaSections.forEach((section) => {
    const sectionElement = document.createElement("section");
    sectionElement.className = "media-section";

    const heading = document.createElement("div");
    heading.className = "media-heading";

    const title = document.createElement("h3");
    title.textContent = section.title;

    const count = document.createElement("p");
    count.className = "date";
    count.textContent = `${section.items.length} images`;

    heading.append(title, count);

    const grid = document.createElement("div");
    grid.className = "media-grid";

    section.items.forEach((item) => {
      const figure = document.createElement("figure");

      const image = document.createElement("img");
      image.src = assetPath(item.path);
      image.alt = item.file;
      image.loading = "lazy";
      image.decoding = "async";

      const caption = document.createElement("figcaption");

      const name = document.createElement("span");
      name.className = "caption-name";
      name.textContent = item.file;

      const date = document.createElement("time");
      date.className = "date";
      date.dateTime = item.date;
      date.textContent = item.date;

      caption.append(name, date);
      figure.append(image, caption);
      grid.append(figure);
    });

    sectionElement.append(heading, grid);
    container.append(sectionElement);
  });
}

renderHeroVideo();
renderMediaSections();
