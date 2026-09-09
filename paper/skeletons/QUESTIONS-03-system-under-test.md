# §3 System Under Test — answer these out loud

Four short paragraphs, ~210 words. The easiest section in the paper: it describes your own
application and makes no argument.

Keep `{{dataset_bytes}}` and `{{dataset_records}}` exactly as written. Keep the code block
and the `[[FIGURE:...]]` line where they are.

---

## Para 1 — what it is (~50 words)

**Facts:** corporate website for an engineering consultancy. Node.js, hand-written HTTP
server, 982 lines, standard library only, no framework, no runtime dependencies. Serves 22
static HTML pages, a small JSON API, 38 MB of static assets.

1. What is this application and who was it built for?
2. How big is it, and what is it built on?
3. What does it actually serve?
4. Why did you test this instead of writing a benchmark app? (the answer is that it's real
   and already deployed — that's the whole point)

---

## Para 2 — the datastore and the missing cache (~50 words)

**Facts:** no database. One JSON file, `{{dataset_bytes}}` bytes, `{{dataset_records}}`
records, 11 collections.

5. Where does it keep its data?
6. Look at this function. What does it do every time it is called, and what does it *not*
   do?

```js
async function getContent() {
  return JSON.parse(await readFile(dataFile, "utf8"));
}
```

7. Why is that absence the reason this application is worth testing?

Mention Fig. 1 somewhere in this paragraph.

---

## Para 3 — why that gives you both variables (~80 words)

The only paragraph doing real work. Answer these in order and you have the chain:

8. The server rewrites HTML for search engines. On how many page requests does that happen?
9. So how often does `getContent()` run for a page request?
10. What else calls it? (content API, search endpoint, sitemap)
11. So what does every one of those requests physically do?
12. `JSON.parse` is synchronous and Node runs JavaScript on one thread. What happens when
    several of those requests overlap?
13. And what happens to a single request's cost when the JSON file gets bigger?
14. So what two things can you now change independently, on one application you didn't
    modify?

---

## Para 4 — the rate limiter (~30 words)

**Facts:** per-IP rate limiting, `/api/search` capped at 30 requests per minute.

15. What limit does the application enforce, and on what?
16. Every virtual user in your test connects from 127.0.0.1. So what does a *per-IP* limit
    become in your test?
17. Point forward to §5.7.

---

## Do not claim

- **Not** that this app is typical or representative of web applications. It is one app.
- **Not** that the missing cache is a bug or bad code. It is a property you are using.
  Call it a defect and someone asks why you didn't just fix it.
- **Not** that you built it for the experiment. It predates the study — that is what makes
  it credible.
- Never name the client or the live site.

## Must appear somewhere in §3 or §4.1

The application under test is a **copy**. The original deployment was never modified. One
four-line change was made to the copy so the rate limiter can be switched off by
environment variable for §5.7, and it is inert when the variable is unset.

(It currently sits in §4.1. Fine to leave it there — just don't lose it.)

---

## When you have written it

```
python scripts/build_paper.py
python scripts/verify_paper.py
```

Send it to me. I check facts, not sentences.
