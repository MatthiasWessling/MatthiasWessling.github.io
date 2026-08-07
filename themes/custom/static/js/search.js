/**
 * Site-wide client-side search (Fuse.js + Hugo index.json).
 */
class SiteSearch {
    constructor() {
        this.root = document.getElementById('site-search');
        this.input = document.getElementById('site-search-input');
        this.resultsEl = document.getElementById('site-search-results');
        this.statusEl = document.getElementById('site-search-status');
        this.openButtons = document.querySelectorAll('[data-search-open]');
        this.fuse = null;
        this.indexPromise = null;
        this.activeIndex = -1;
        this.results = [];
        this.isOpen = false;

        if (!this.root || !this.input || !this.resultsEl) {
            return;
        }

        this.bindEvents();
    }

    bindEvents() {
        this.openButtons.forEach((btn) => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                this.open();
            });
        });

        this.root.querySelectorAll('[data-search-close]').forEach((el) => {
            el.addEventListener('click', () => this.close());
        });

        this.input.addEventListener('input', this.debounce(() => this.query(this.input.value), 120));

        this.input.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowDown') {
                e.preventDefault();
                this.moveActive(1);
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                this.moveActive(-1);
            } else if (e.key === 'Enter') {
                if (this.activeIndex >= 0 && this.results[this.activeIndex]) {
                    e.preventDefault();
                    const item = this.results[this.activeIndex].item;
                    const href = item.permalink;
                    if (/^https?:\/\//i.test(href)) {
                        window.open(href, '_blank', 'noopener,noreferrer');
                    } else {
                        window.location.href = href;
                    }
                }
            }
        });

        document.addEventListener('keydown', (e) => {
            const isModK = (e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k';
            if (isModK) {
                e.preventDefault();
                if (this.isOpen) {
                    this.close();
                } else {
                    this.open();
                }
                return;
            }

            if (e.key === 'Escape' && this.isOpen) {
                e.preventDefault();
                e.stopPropagation();
                this.close();
            }
        });
    }

    async open() {
        this.isOpen = true;
        this.root.hidden = false;
        document.body.classList.add('site-search-open');
        this.input.focus();
        this.input.select();
        this.setStatus('Loading index…');
        try {
            await this.ensureIndex();
            if (this.input.value.trim()) {
                this.query(this.input.value);
            } else {
                this.setStatus('Multiple terms are AND’d. Quote phrases: "ion transport".');
                this.resultsEl.innerHTML = '';
            }
        } catch (err) {
            console.error('Search index failed to load', err);
            this.setStatus('Search is temporarily unavailable.');
        }
    }

    close() {
        this.isOpen = false;
        this.root.hidden = true;
        document.body.classList.remove('site-search-open');
        this.activeIndex = -1;
    }

    async ensureIndex() {
        if (this.fuse) {
            return this.fuse;
        }
        if (!this.indexPromise) {
            this.indexPromise = this.loadFuseAndIndex();
        }
        this.fuse = await this.indexPromise;
        return this.fuse;
    }

    async loadFuseAndIndex() {
        await this.loadFuse();
        const indexUrl = this.root.dataset.indexUrl || '/index.json';
        const res = await fetch(indexUrl, { credentials: 'same-origin' });
        if (!res.ok) {
            throw new Error(`HTTP ${res.status} for ${indexUrl}`);
        }
        const data = await res.json();

        return new window.Fuse(data, {
            includeScore: true,
            shouldSort: true,
            threshold: 0.35,
            ignoreLocation: true,
            minMatchCharLength: 2,
            useExtendedSearch: true,
            keys: [
                { name: 'title', weight: 0.34 },
                { name: 'keywords', weight: 0.18 },
                { name: 'authors', weight: 0.14 },
                { name: 'extra', weight: 0.12 },
                { name: 'journal', weight: 0.08 },
                { name: 'summary', weight: 0.06 },
                { name: 'doi', weight: 0.04 },
                { name: 'content', weight: 0.02 },
                { name: 'sectionLabel', weight: 0.02 }
            ]
        });
    }

    loadFuse() {
        if (window.Fuse) {
            return Promise.resolve();
        }
        return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = 'https://cdn.jsdelivr.net/npm/fuse.js@7.0.0/dist/fuse.min.js';
            script.async = true;
            script.onload = () => resolve();
            script.onerror = () => reject(new Error('Failed to load Fuse.js'));
            document.head.appendChild(script);
        });
    }

    /**
     * Build a Fuse extended-search query.
     * Space-separated terms are AND'd; "quoted phrases" stay together.
     * Example: membrane "ion concentration" → must match both.
     */
    buildExtendedQuery(raw) {
        const terms = [];
        const tokenRe = /"([^"]+)"|(\S+)/g;
        let match;
        while ((match = tokenRe.exec(raw)) !== null) {
            const term = (match[1] || match[2] || '').trim();
            if (term.length < 2) {
                continue;
            }
            // Escape Fuse extended-search operators inside the term.
            const escaped = term.replace(/([\\'"|=!$^])/g, '\\$1');
            terms.push(`'${escaped}`);
        }
        return terms.join(' ');
    }

    query(raw) {
        const q = raw.trim();
        this.activeIndex = -1;

        if (!this.fuse) {
            this.setStatus('Loading index…');
            return;
        }

        const fuseQuery = this.buildExtendedQuery(q);
        if (!fuseQuery) {
            this.results = [];
            this.resultsEl.innerHTML = '';
            this.setStatus(q.length ? 'Keep typing…' : 'Multiple terms are AND’d. Quote phrases: "ion transport".');
            return;
        }

        this.results = this.fuse.search(fuseQuery, { limit: 40 });
        this.renderResults(q);
    }

    renderResults(q) {
        if (!this.results.length) {
            this.resultsEl.innerHTML = '';
            this.setStatus(`No results for “${q}”.`);
            return;
        }

        const paperCount = this.results.filter((hit) => hit.item.kind === 'paper').length;
        const statusBits = [`${this.results.length} result${this.results.length === 1 ? '' : 's'}`];
        if (paperCount) {
            statusBits.push(`${paperCount} paper${paperCount === 1 ? '' : 's'}`);
        }
        this.setStatus(statusBits.join(' · '));

        this.resultsEl.innerHTML = this.results.map((hit, i) => {
            const item = hit.item;
            const isPaper = item.kind === 'paper';
            const isExternal = /^https?:\/\//i.test(item.permalink || '');
            let snippet = '';
            if (isPaper) {
                const meta = [item.journal, item.year, item.authors].filter(Boolean).join(' · ');
                const kw = String(item.keywords || '')
                    .split(';')
                    .map((s) => s.trim())
                    .filter(Boolean)
                    .slice(0, 6)
                    .join('; ');
                snippet = this.escapeHtml([meta, kw].filter(Boolean).join(' · '));
            } else {
                snippet = this.snippet(item.summary || item.content || '', q);
            }
            const source = isPaper && item.sourceTitle
                ? `<span class="site-search-result-source">via <span class="site-search-result-source-name">${this.escapeHtml(item.sourceTitle)}</span></span>`
                : '';
            const externalAttrs = isExternal ? ' target="_blank" rel="noopener noreferrer"' : '';

            return `
                <li class="site-search-result${isPaper ? ' is-paper' : ''}" role="option" data-index="${i}">
                    <a href="${this.escapeAttr(item.permalink)}" class="site-search-result-link"${externalAttrs}>
                        <span class="site-search-result-section">${this.escapeHtml(item.sectionLabel || item.section || 'Page')}</span>
                        <span class="site-search-result-title">${this.escapeHtml(item.title)}</span>
                        ${snippet ? `<span class="site-search-result-snippet">${snippet}</span>` : ''}
                        ${source}
                    </a>
                </li>
            `;
        }).join('');

        this.resultsEl.querySelectorAll('.site-search-result').forEach((li) => {
            li.addEventListener('mouseenter', () => {
                this.setActive(Number(li.dataset.index));
            });
        });
    }

    snippet(text, q) {
        const clean = String(text || '').replace(/\s+/g, ' ').trim();
        if (!clean) {
            return '';
        }
        const lower = clean.toLowerCase();
        const needle = q.toLowerCase().split(/\s+/).find((t) => t.length >= 2) || q.toLowerCase();
        let idx = lower.indexOf(needle);
        if (idx < 0) {
            idx = 0;
        }
        const start = Math.max(0, idx - 40);
        const end = Math.min(clean.length, idx + needle.length + 80);
        let excerpt = clean.slice(start, end);
        if (start > 0) {
            excerpt = `…${excerpt}`;
        }
        if (end < clean.length) {
            excerpt = `${excerpt}…`;
        }
        return this.escapeHtml(excerpt);
    }

    moveActive(delta) {
        if (!this.results.length) {
            return;
        }
        const next = (this.activeIndex + delta + this.results.length) % this.results.length;
        this.setActive(next);
    }

    setActive(index) {
        this.activeIndex = index;
        const items = this.resultsEl.querySelectorAll('.site-search-result');
        items.forEach((el, i) => {
            el.classList.toggle('is-active', i === index);
            if (i === index) {
                el.scrollIntoView({ block: 'nearest' });
            }
        });
    }

    setStatus(message) {
        if (this.statusEl) {
            this.statusEl.textContent = message;
        }
    }

    escapeHtml(str) {
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
    }

    escapeAttr(str) {
        return this.escapeHtml(str).replace(/'/g, '&#39;');
    }

    debounce(fn, wait) {
        let timer;
        return (...args) => {
            clearTimeout(timer);
            timer = setTimeout(() => fn.apply(this, args), wait);
        };
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.siteSearch = new SiteSearch();
});
