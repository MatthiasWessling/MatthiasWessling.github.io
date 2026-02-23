# Personal GitHub Pages Website

This repository contains a simple personal website inspired by the style of:
- https://flowsnr.github.io/index.html

## Edit content in Cursor

Open `script.js` and edit the `siteContent` object at the top:
- Name, intro, bio, email
- Social links
- News entries
- Blog posts
- Research/project/hobby text
- CV link (`cvUrl`)

No framework is required. This is plain HTML/CSS/JS.

## Preview locally

You can open `index.html` directly in your browser, or run:

```bash
python3 -m http.server 8080
```

Then visit `http://localhost:8080`.

## Publish to GitHub Pages

### Option A: User site (`<username>.github.io`)

1. Create a GitHub repository named exactly `<username>.github.io`
2. Run these commands in this project folder:

```bash
git init
git add .
git commit -m "Initial personal website"
git branch -M main
git remote add origin git@github.com:<username>/<username>.github.io.git
git push -u origin main
```

Your site will be live at:
- `https://<username>.github.io`

### Option B: Project site

1. Create any repository name (for example `personal-site`)
2. Push with:

```bash
git init
git add .
git commit -m "Initial personal website"
git branch -M main
git remote add origin git@github.com:<username>/personal-site.git
git push -u origin main
```

3. In GitHub repository settings:
- Go to **Pages**
- Source: **Deploy from a branch**
- Branch: `main` and folder `/ (root)`

Your site will be:
- `https://<username>.github.io/personal-site/`
