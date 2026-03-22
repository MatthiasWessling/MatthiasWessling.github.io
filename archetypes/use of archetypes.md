Updated archetypes/news.md with a more useful default template.
What changed:
Added optional taxonomy fields:
tags = []
categories = []
Replaced generic body text with a clearer scaffold:
intro placeholder
## Why this matters
## Key points
## Link
How to use it now:
Run hugo new news/my-next-update.md
Fill in front matter + section placeholders
Preview on http://localhost:1313
Set draft = false when ready to publish
If you want, I can similarly upgrade archetypes/notebooks.md to match the same style and include stronger defaults for notebooklm_url and media fields.
