# §3 System Under Test — skeleton

Target: ~210 words. Four short paragraphs. This is the easiest section in the paper:
it describes your own application, and there is no argument to make yet.

Rules: use the placeholders `{{dataset_bytes}}` and `{{dataset_records}}` exactly as
written — the build fills them. Leave the code block and the `[[FIGURE:...]]` line
where they are. Do not copy sentences from the current draft; work from the facts.

---

## Para 1 — what the application is

Facts:

- corporate website for an engineering consultancy
- Node.js, hand-written HTTP server
- 982 lines
- standard library only. no framework, no runtime dependencies
- serves: 22 static HTML pages, a small JSON API, 38 MB of static assets

You are answering: *what is this thing, and is it real?*

The point of this paragraph is that it's a real deployed application, not a benchmark
toy someone wrote to produce a result.

---

## Para 2 — the datastore and the missing cache

Facts:

- no database
- datastore is one JSON file
- `{{dataset_bytes}}` bytes
- `{{dataset_records}}` records
- across 11 collections

Then introduce the code block (keep it as-is):

```js
async function getContent() {
  return JSON.parse(await readFile(dataFile, "utf8"));
}
```

You are answering: *what is the one property of this app that makes it worth testing?*

Answer in your own words: there is no cache. Every call re-reads the file and re-parses it.

Keep `Fig. 1` referenced somewhere in this paragraph.

---

## Para 3 — why that property gives you both variables

This is the only paragraph that does real work. Chain of reasoning, in order:

1. the server rewrites HTML for search engines on every page request
2. → so `getContent()` runs for every page request
3. → it also runs for the content API, the search endpoint, and the sitemap
4. → so every request does a file read plus a synchronous `JSON.parse`
5. → `JSON.parse` is synchronous, and Node's event loop is single-threaded
6. → therefore: per-request cost becomes queueing when requests overlap
7. → and: dataset size becomes per-request cost

Conclusion to land: both independent variables this study needs (**concurrency** and
**per-request cost**) are available on one unmodified application.

You are answering: *why is this app a good instrument rather than just a convenient one?*

---

## Para 4 — the rate limiter

Facts:

- per-IP rate limiting
- `/api/search` capped at 30 requests per minute
- all load originates from one address
- → so a per-IP limit behaves as a system-wide limit
- forward-reference it to §5.7

Short. Two or three sentences. It exists to set up Arm B later.

---

## Do not claim

- **Not** that this app is "typical" or "representative" of web applications. It is one
  application. n=1. §7 already admits this.
- **Not** that the missing cache is a bug, bad code, or a mistake. It is a property you
  are making use of. Calling it a defect invites "why not just fix it".
- **Not** that you built it for the experiment. It predates the study. That is what makes
  it credible.
- Do **not** name the client or the site anywhere in the paper.

## Must mention somewhere in §3 or §4.1

- the application under test is a **copy**; the original deployment was never modified
- one four-line change was made to the copy so the rate limiter can be switched off by
  environment variable for §5.7; the change is inert when the variable is unset

(Currently this sits in §4.1. Fine to leave it there — just don't lose it.)

---

## When you are done

```
python scripts/build_paper.py
python scripts/verify_paper.py
```

Build fails if you break a placeholder. Tell me when it's written and I'll check it
against `facts.json` for anything that contradicts the data.
