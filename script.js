const siteContent = {
  name: "Matthias Wessling",
  title: "Matthias Wessling | Personal Website",
  intro: "Welcome to my personal website.",
  bio: "I share updates about my projects, learning progress, and technical interests. This page is intentionally simple and easy to update in Cursor.",
  email: "matthias.wessling@example.com",
  footer: "© 2026 Matthias Wessling. All rights reserved.",
  cvUrl: "cv.pdf",
  socialLinks: [
    { label: "GitHub", url: "https://github.com/MatthiasWessling" }
  ],
  news: [
    {
      date: "Feb 23, 2026",
      title: "Launched personal GitHub Pages website",
      description: "Set up and published my personal site from a local Cursor project."
    },
    {
      date: "Jan 15, 2026",
      title: "Portfolio refresh in progress",
      description: "Currently updating project descriptions and adding better documentation."
    }
  ],
  blogPosts: [
    {
      date: "Feb 23, 2026",
      title: "Building a personal site with Cursor and GitHub Pages",
      description: "A short walkthrough of setting up a clean static site and publishing it.",
      tags: ["cursor", "github-pages", "web"]
    },
    {
      date: "Feb 10, 2026",
      title: "What I want to improve this year",
      description: "Notes on technical goals, writing more, and shipping small projects consistently.",
      tags: ["learning", "career", "projects"]
    }
  ],
  research: [
    "I am interested in practical software engineering, developer tooling, and reliable automation.",
    "I use this section to capture what I am currently exploring and experimenting with."
  ],
  projects: [
    {
      title: "Test",
      description: "Wolfram modules and experiments.",
      link: "https://github.com/MatthiasWessling/Test"
    },
    {
      title: "Personal Website",
      description: "Source code for this GitHub Pages website.",
      link: "https://github.com/MatthiasWessling/MatthiasWessling.github.io"
    }
  ],
  hobbies: [
    "I enjoy coding side projects and learning new tools.",
    "I also like walking, fitness, and working on practical ideas end-to-end."
  ]
};

function byId(id) {
  return document.getElementById(id);
}

function renderCards(containerId, items, cardRenderer) {
  const container = byId(containerId);
  container.innerHTML = "";
  items.forEach((item) => {
    const card = document.createElement("article");
    card.className = "card";
    card.innerHTML = cardRenderer(item);
    container.appendChild(card);
  });
}

function renderSite() {
  document.title = siteContent.title;
  byId("siteTitle").textContent = siteContent.name;
  byId("heroName").textContent = siteContent.name;
  byId("heroIntro").textContent = siteContent.intro;
  byId("heroBio").textContent = siteContent.bio;
  byId("footerText").textContent = siteContent.footer;

  const emailLink = byId("emailLink");
  emailLink.textContent = siteContent.email;
  emailLink.href = `mailto:${siteContent.email}`;

  const cvLink = byId("cvLink");
  cvLink.href = siteContent.cvUrl;

  const social = byId("socialLinks");
  social.innerHTML = "";
  siteContent.socialLinks.forEach((entry) => {
    const a = document.createElement("a");
    a.href = entry.url;
    a.textContent = entry.label;
    a.target = "_blank";
    a.rel = "noopener";
    social.appendChild(a);
  });

  renderCards("newsList", siteContent.news, (item) => `
    <p class="meta">${item.date}</p>
    <h3>${item.title}</h3>
    <p>${item.description}</p>
  `);

  renderCards("blogList", siteContent.blogPosts, (item) => `
    <p class="meta">${item.date}</p>
    <h3>${item.title}</h3>
    <p>${item.description}</p>
    <div class="tags">
      ${item.tags.map((tag) => `<span class="tag">${tag}</span>`).join("")}
    </div>
  `);

  byId("researchText").innerHTML = siteContent.research
    .map((line) => `<p>${line}</p>`)
    .join("");

  renderCards("projectsList", siteContent.projects, (item) => `
    <h3>${item.title}</h3>
    <p>${item.description}</p>
    <p><a href="${item.link}" target="_blank" rel="noopener">View project</a></p>
  `);

  byId("hobbiesText").innerHTML = siteContent.hobbies
    .map((line) => `<p>${line}</p>`)
    .join("");
}

function wireMenu() {
  const button = byId("menuBtn");
  const nav = document.querySelector(".nav");
  button.addEventListener("click", () => {
    nav.classList.toggle("open");
  });
}

renderSite();
wireMenu();
