# System Under Test — Deltadesh corporate website

Discovery report for the web-application performance study.
Written **2026-08-24**. Task 1 only — nothing has been started, modified or requested yet.

Everything below was read from source. Where something is ambiguous it is marked
**AMBIGUOUS** rather than resolved by assumption.

---

## 0. Which copy is the SUT

Seven Deltadesh directories exist on this machine. They are not equivalent.

| Path | What it is |
|---|---|
| **`C:\Users\USER\Documents\deltadesh-website-render`** | **The real application.** 82 MB, git repo, full server. **This is the SUT.** |
| `C:\Users\USER\audits\deltadesh` | A single 27 KB audit text file. Not code. |
| `C:\Users\USER\OneDrive\Documents\deltadesh-redesign-demo` | 6.3 MB static redesign mock-up. No server. |
| `C:\Users\USER\OneDrive\Pictures\deltadesh-redesign-demo` | Duplicate of the above. |
| `F:\MovedFromC\UserProjects\deltadesh` | Older copy. |
| `F:\projects\deltadesh-website-render` | Another copy. |
| `D:\Personal\Documents\deltadesh-redesign-demo` | Another copy of the mock-up. |

> ### SAFETY FLAG — this directory is the live site's deploy source
>
> ```
> origin  https://github.com/abedinm/deltadesh-website.git
> branch  main   (working tree clean)
> ```
>
> It deploys to Render (Frankfurt) and serves **deltadesh.com**, a real client's live
> site. Consequences that shape the whole study:
>
> - **No file in this directory should be modified.** A change committed and pushed
>   reaches production.
> - **Load-testing POST endpoints against this directory writes into its `data/`
>   folder.** `data/submissions/` already holds 3 real submissions. Hammering
>   `/api/contact` would write thousands of files into the live repo's data directory.
> - **Recommendation:** copy the app to `perf-web/sut/` and run the copy. The study then
>   cannot touch the client's repo, and any experimental change to the copy is a
>   documented control rather than a risk. **Awaiting your decision — I have not copied
>   or modified anything.**

Two other copies of this same repo exist (`F:\projects\`, `F:\MovedFromC\`). They have not
been diffed; if either is a detached scratch copy it might be a safer base than a fresh
copy. **AMBIGUOUS — say which you prefer.**

---

## 1. Static site, or a backend?

**There is a backend.** This is not a static site.

| Property | Value |
|---|---|
| Language / runtime | **JavaScript on Node.js**, ESM (`"type": "module"`) |
| Node version installed | **v24.15.0** (npm 11.12.1) |
| Node version targeted | `NODE_VERSION=24` in `render.yaml` |
| Framework | **None.** Hand-rolled HTTP server |
| Runtime dependencies | **Zero** |
| Server file | `serve.mjs`, 982 lines |

`serve.mjs` imports only Node built-ins:

```js
node:http, node:fs/promises, node:fs, node:path, node:url, node:crypto
```

No Express, no Fastify, no framework of any kind. `package.json` lists only
*devDependencies* (eslint, prettier, sharp, supabase CLI) — none are loaded at runtime.

The server does three jobs: serves static files, exposes a small JSON API, and performs
**server-side SEO injection** into HTML before sending it. That third job is the one that
matters most for this study — see §5.

---

## 2. Database

**There is no database in use.** The datastore is a single JSON file.

| | |
|---|---|
| Store | `data/content.json` |
| Size | **88,826 bytes (~87 KB)** |
| Access | `JSON.parse(await readFile(dataFile, "utf8"))` on every call |
| DB client imported | **none** |

`.env.example` does reference PostgreSQL and Supabase:

```
DATABASE_URL=postgresql://USER:PASSWORD@HOST:5432/deltadesh
SUPABASE_URL=...
```

but the comment above it reads *"(Supabase / PostgreSQL — when ready to migrate from
JSON)"*. A `supabase/` directory and a `database/` directory exist in the repo. **No
Postgres driver is imported by `serve.mjs`, and no database connection is opened
anywhere in it.** The Supabase material is preparation for a future migration that has
not happened.

> **This changes the study's framing.** There is no DB tier to blame. Every request that
> needs content pays for a **filesystem read plus a synchronous `JSON.parse`**, and
> `JSON.parse` blocks Node's single event-loop thread. That is the tail-latency mechanism
> here, and it is a cleaner one to write about than a database, because there is no
> connection pool or query planner confounding it.

### Which pages actually read the store

**Almost all of them**, which is not obvious from the outside:

| Consumer | Line | Reads `content.json`? |
|---|---|---|
| Every HTML page serve (via `injectSEO`) | 945 | **Yes — every single request** |
| `GET /api/content` | 652 | Yes |
| `GET /api/search` | 659 | Yes |
| `GET /sitemap.xml` | 841 | Yes |
| Static assets (images, CSS, JS) | — | No |

`getContent()` in full:

```js
async function getContent() {
  return JSON.parse(await readFile(dataFile, "utf8"));
}
```

**No caching, no memoisation, no `fs.watch` invalidation.** Loading `services.html` re-reads
and re-parses 87 KB of JSON. So does loading it again one millisecond later.

---

## 3. How it is meant to be served

| Manifest | Present | Contents |
|---|---|---|
| `package.json` | Yes | `"start": "node serve.mjs"`, `"dev": "node serve.mjs"` |
| `render.yaml` | Yes | Render web service, Node, Frankfurt, `npm install` → `npm start` |
| `start-server.bat` | Yes | Local Windows launcher, sets `PORT=8083` |
| `docker-compose.yml` | **No** | — |
| `Dockerfile` | **No** | — |
| `requirements.txt` | **No** | — |
| `Procfile` | **No** | — |

Port resolution (`serve.mjs:31`):

```js
const port = Number(process.env.PORT ?? 8080);
```

So: **`PORT=<n> node serve.mjs`**, defaulting to 8080. `start-server.bat` uses 8083.
`.claude/launch.json` on this machine also defines a `deltadesh-deploy` entry on 8139.

### Environment variables that change behaviour

| Variable | Default | Effect if unset |
|---|---|---|
| `PORT` | 8080 | — |
| `DATA_DIR` | `./data` | Falls back to repo `data/` — **the live repo's data folder** |
| `ADMIN_TOKEN` | unset | Admin endpoints unusable (fine — not under test) |
| `TRUST_PROXY` | `false` | Rate limiting keys on the socket IP. Correct for local |
| `RESEND_API_KEY` | unset | **No local `.env` exists**, so no key, so **no email is sent** |

**Checked: there is no `.env` file in the directory.** No secrets are present locally and
no outbound email can fire. Form posts "still save to disk silently" per the template's own
comment — they write files, they do not send mail.

---

## 4. Route inventory

### 4.1 JSON API (`serve.mjs`)

| Method | Route | Line | Auth | Rate limit |
|---|---|---|---|---|
| GET | `/api/content` | 651 | no | **none** |
| GET | `/api/search?q=` | 656 | no | **30 / 60 s** |
| POST | `/api/contact` | 669 | no | **5 / 10 min** |
| POST | `/api/careers` | 686 | no | **5 / 10 min** |
| POST | `/api/track` | 703 | no | **60 / 60 s** |
| POST | `/api/admin/content` | 715 | token | ADMIN bucket |
| GET | `/api/admin/backup` | 727 | token | ADMIN bucket |
| GET | `/api/admin/submissions` | 739 | token | ADMIN bucket |
| POST | `/api/admin/upload` | 753 | token | ADMIN bucket |
| GET | `/api/admin/analytics-summary` | 822 | token | ADMIN bucket |
| GET | `/sitemap.xml` | 840 | no | none |
| GET | `/robots.txt` | 860 | no | none |

### 4.2 HTML pages (22, all served through `injectSEO`)

`index.html` (25 KB), `people.html` (10.7 KB), `maturity-index.html` (9.6 KB),
`privacy.html` (8.0 KB), `how-we-work.html` (7.4 KB), `careers.html`, `contact.html`,
`insights.html`, `news.html`, `sectors.html`, `services.html`, `projects.html`,
`clients.html`, `search.html`, `gallery.html`, `profile.html`, `sector.html`,
`project-detail.html`, `insight-detail.html`, `news-detail.html`, `risk-control.html`,
`admin.html` (skipped by `injectSEO`).

Four are **query-parameter driven**, and the parameter changes the injected HTML:

| Page | Parameter | Line |
|---|---|---|
| `project-detail.html` | `?project=<slug>` | 317 |
| `sector.html` | `?sector=<id>` | 334 |
| `insight-detail.html` | `?insight=<slug>` | 345 |
| `news-detail.html` | `?news=<slug>` | 356 |

### 4.3 Static assets

`assets/` is **38 MB across 253 image files**. Served with
`Cache-Control: public, max-age=31536000, immutable`. HTML/CSS/JS are served `no-cache`
(deliberate, per an in-file comment about edits not taking effect).

---

## 5. Which routes are plausibly slowest — and by what mechanism

Ranked by mechanism read from the source, not by guesswork.

**1. `GET /api/search?q=…` — the strongest candidate**

Per request it does *all* of:

```js
const content  = await getContent();                    // read 87 KB + JSON.parse
const records  = flattenSearch(content);                // rebuild ~174 objects, every time
const results  = records.filter(item =>                 // O(n) substring scan
    `${item.title} ${item.body}`.toLowerCase().includes(query));
if (query) logAnalytics({ ... });                       // a DISK WRITE per search
```

No index, no cached flatten, and a write on the read path. Four costs stacked on one
endpoint.

**2. Every HTML page — the non-obvious one**

`injectSEO` at line 945 calls `getContent()`, so **every** page load pays the read +
parse, then runs regex rewrites over the HTML. `index.html` is the largest at 25 KB. This
is the finding most likely to be invisible to average-response-time reporting, because it
is fast when idle and degrades only under concurrency, when synchronous `JSON.parse` calls
queue behind each other on the single event-loop thread.

**3. `GET /sitemap.xml`** — reads content and builds XML over all records.

**4. `POST /api/contact` / `/api/careers`** — parse, validate, write a file to disk.
Untestable under load (see §6) and they write into the live repo's data directory.

**5. Image-heavy pages** (`gallery`, `projects`, `clients`, `people`) — many static file
reads, but no JSON parse and immutable caching. Bandwidth-bound, not CPU-bound. Least
interesting for tail latency.

---

## 6. Blocking issue for load testing: the rate limiter

`serve.mjs:101` defines per-IP limits:

```js
const RATE_LIMITS = {
  "POST /api/contact": { max: 5,  windowMs: 10 * 60 * 1000 },
  "POST /api/careers": { max: 5,  windowMs: 10 * 60 * 1000 },
  "POST /api/track":   { max: 60, windowMs: 60 * 1000 },
  "GET /api/search":   { max: 30, windowMs: 60 * 1000 },
  "ADMIN":             { max: 10, windowMs: 10 * 60 * 1000 }
};
```

**A load test from localhost is a single IP, so every virtual user shares one bucket.**

| Route | Effective ceiling | Consequence |
|---|---|---|
| `GET /api/search` | **30 requests/minute** | The most interesting route saturates in seconds, then returns 429 |
| `POST /api/contact` | **5 per 10 minutes** | Not load-testable at all |
| `POST /api/careers` | **5 per 10 minutes** | Not load-testable at all |
| `POST /api/track` | 60/minute | 1 req/s ceiling |
| **HTML pages, `/api/content`, `/sitemap.xml`** | **unlimited** | **Fully testable** |

This is worth stating plainly because of how it would fail: **429 responses are fast.**
A test that trips the limiter produces *better* average response times while the
application does no work at all. The mean would improve as the system stopped
functioning — which is, ironically, a sharper illustration of your thesis than anything
you planned to measure, but only if it is deliberate rather than accidental.

Four ways forward, none of which I will pick for you:

1. **Test only the unlimited routes.** Zero modification. HTML pages and `/api/content`
   still exercise the read + parse + event-loop mechanism, which is the real story.
2. **Treat the limiter as part of the SUT** and report 429 onset as a documented finding.
3. **Copy the app to `perf-web/sut/` and disable the limiter in the copy**, recorded as an
   experimental control. The live repo stays untouched. This is not "tuning to make
   numbers look better" — it removes an artificial gate to expose the application
   underneath — but it is your call to make, not mine.
4. **Rebind the limiter key** so virtual users are separate buckets. Also a code change,
   also copy-only.

My recommendation: **(1) for the headline experiment, plus (3) as a separate documented
arm** so search can be characterised too. Say which you want.

---

## 7. Dataset volume — read this before Task 2

`data/content.json` holds **188 records** across 11 top-level keys:

| Key | Records |
|---|---|
| clients | 70 |
| people | 41 |
| projects | 38 |
| services | 12 |
| sectors | 6 |
| gallery | 6 |
| insights | 5 |
| testimonials_unverified | 4 |
| awards_unverified | 4 |
| news | 2 |
| company | object, 9 keys |

`flattenSearch()` builds **174 searchable records** per search request.

**This is real client data, not an empty scaffold — but it is small.** You asked to be told
if a near-empty datastore would make results meaningless. The honest position:

- **Not meaningless, but understated.** The per-request cost is dominated by
  `readFile` + `JSON.parse` of 87 KB, which is real and *does* scale with concurrency
  regardless of record count, because the parse is synchronous and single-threaded.
- **The O(n) search scan will not show up at 174 records.** Scanning 174 short strings is
  microseconds. To make search's algorithmic weakness visible you would need on the order
  of 10⁴–10⁵ records.
- **Recommendation:** run the baseline against the real 87 KB dataset first — that is the
  production-truthful measurement — then add a **scaled-dataset arm** (synthetic records
  at, say, 10×, 100×, 1000×) to show tail latency growing while the mean stays flat. That
  comparison is a stronger paper result than either alone.

Generating synthetic volume means writing a `content.json` variant. **It must not be
written into the live repo's `data/` directory.** Another reason to work from a copy.

---

## 8. Ambiguities and open questions

1. **Which working copy to use.** Recommend copying to `perf-web/sut/`; the live repo
   should not be the SUT. **Needs your decision.**
2. **Rate limiter policy.** Four options in §6. **Needs your decision.**
3. **Dataset scaling.** Baseline-only, or baseline plus scaled arm. **Needs your decision.**
4. **`database/` and `supabase/` directories** exist but are not loaded by `serve.mjs`.
   Not inspected in depth — they appear to be migration groundwork. Flagging rather than
   asserting they are dead.
5. **`sw.js` (service worker)** is present. Irrelevant to k6 (no browser cache involved),
   but it means browser-observed behaviour and k6-observed behaviour will differ. Worth a
   sentence in threats to validity.
6. **HTML/CSS/JS are served `no-cache`** by deliberate choice. Load results will therefore
   reflect zero client caching, which is realistic for k6 but pessimistic versus real
   browsers.

---

## 9. Nothing has been started

Per the Task 1 instruction, discovery only:

- No server started.
- No file in the Deltadesh directory read into, written to, or modified. `git status` is
  clean and stays clean.
- No k6 installed yet.
- No request issued to any host, local or remote.
