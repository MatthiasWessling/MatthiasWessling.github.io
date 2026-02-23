const siteContent = {
  name: "Your Name",
  title: "Your Name | Personal Website",
  intro: "I am interested in artificial intelligence, research, and building practical tools.",
  bio: "Use this website to share your work, thoughts, projects, and updates. Edit this text in script.js.",
  email: "you@example.com",
  footer: "© 2026 Your Name. All rights reserved.",
  cvUrl: "cv.pdf",
  socialLinks: [
    { label: "GitHub", url: "https://github.com/your-username" },
    { label: "LinkedIn", url: "https://linkedin.com/in/your-profile" },
    { label: "Google Scholar", url: "https://scholar.google.com/" },
    { label: "X", url: "https://x.com/your-handle" }
  ],
  news: [
    {
      date: "Feb 18, 2026",
      title: "Example milestone",
      description: "Add your latest announcement or achievement here."
    },
    {
      date: "Jul 27, 2025",
      title: "Example conference/project update",
      description: "Share notable updates in chronological order."
    }
  ],
  blogPosts: [
    {
      date: "Feb 9, 2026",
      title: "Using Agents to Assist Research Tasks",
      description: "Write a short summary of the post and link to a full article if needed.",
      tags: ["education", "machine-learning", "ai-agents"]
    },
    {
      date: "Oct 17, 2025",
      title: "Recap: More than 20 students supervised",
      description: "Describe your key takeaway in one sentence.",
      tags: ["education", "supervision", "student-research"]
    }
  ],
  research: [
    "Summarize your current research focus.",
    "Explain what problems you are working on and why they matter."
  ],
  projects: [
    {
      title: "Project One",
      description: "One line about the project goal and impact.",
      link: "https://github.com/your-username/project-one"
    },
    {
      title: "Project Two",
      description: "Another project or demo.",
      link: "https://github.com/your-username/project-two"
    }
  ],
  hobbies: [
    "List hobbies you enjoy outside work.",
    "Example: hiking, coding side projects, fitness, photography."
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
