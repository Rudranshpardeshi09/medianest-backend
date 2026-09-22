# MediaNest — Backend Implementation Plan

Audited against the frontend working tree on 2026-09-22, at commit `e7ae6e6`.
Companion to `BACKEND-PLAN.md`, which defines *what* should be dynamic.
This document defines *how* to build it.

**Phase 0 is built. Everything from Phase 1 on is not.**

## Repository layout

Two separate repositories, deployed to two platforms:

| | Folder | Deploys to |
|---|---|---|
| Frontend | `Desktop/medianest` | Vercel (unchanged, still builds from the repo root) |
| Backend | `Desktop/medianest-backend` | Railway |

Frontend paths in this document (`src/components/...`) are relative to the
**frontend** repo root. Backend paths are relative to this one.

They were briefly a single monorepo with `frontend/` and `backend/` folders.
That was reverted: it would have forced a change to the existing Vercel
project and made both platforms rebuild on every commit to either side.

---

## 0. Findings that contradict the brief

The task brief assumed several things that do not exist in this repository.
Stating them first, because three of them change the plan.

| Brief assumed | Actually in the repo |
|---|---|
| "Django backend or partially created Django backend" | **No backend of any kind.** No `manage.py`, `settings.py`, `requirements.txt`, `pyproject.toml` |
| "PostgreSQL configuration" | **None.** No database config, no `.env`, no Docker |
| "`agency-agent/` containing reusable skills" | **Does not exist** |
| "`BACKEND-PLAN(1).md`" | Only `BACKEND-PLAN.md` exists. Treated as the same document |
| 9 REST endpoints | `BACKEND-PLAN.md` specifies **2**. See §11 and Decision Gate 2 |
| "P0/P1/P2 roadmap" in the source document | `BACKEND-PLAN.md` has a **3-step build order**, not P0/P1/P2. Mapped in §19 |
| Slugs on Discipline | No detail pages exist. See Decision Gate 4 |

This is a **greenfield backend against a finished, deployed frontend**. That is
a simpler job than the brief implies, and a riskier one in exactly one respect
— see §5 and Decision Gate 1.

---

## 1. Current architecture

```
  Browser
     |
  Vercel (static hosting)
     |
  index.html  ->  /assets/index-*.js  +  /assets/index-*.css
     |
  React 19 SPA, client-rendered
     |
  every value is a hardcoded const in a .jsx module
```

There is no server, no API, no database, no environment variable plumbing.
`grep -rn "import.meta.env" src/` returns nothing.

**Stack:** React 19.1.1 · Vite 7.1.5 · framer-motion 13.2.0.
`react-router-dom` 7.8.2 is a declared dependency but **nothing in the shipped
app imports it** — only the parked `src/future/` scaffold does. It never
reaches the bundle.

**Build:** `vite build` → `dist/`. Three scripts only: `dev`, `build`,
`preview`. No test runner, no linter config.

---

## 2. Existing frontend architecture

One page. No routes. `main.jsx → App.jsx` renders in this order:

| # | Component | Section id | Content source |
|---|---|---|---|
| — | `Header` | — | `NAV`, `SOCIAL` consts |
| — | `MediaNestIntro` | — | 240 JPGs + measured constants |
| 1 | `Hero` | `home` | `LINES`, `SHEET`, `NOTES` consts |
| 2 | `About` | `about` | `PILLARS`, `STATS` consts |
| 3 | `WhatWeOffer` | — | `DISCIPLINES` const |
| 4 | `Services` | `services` | `SERVICES`, `MORE` consts |
| 5 | `Portfolio` | `projects` | `WORK` from `src/lib/work.js` |
| 6 | `WhyChoose` | — | `REASONS` const |
| 7 | `Team` | `team` | `FOUNDERS` const |
| 8 | `Testimonials` | `video` | `QUOTES` const |
| 9 | `Clients` | `clients` | `CLIENTS` const |
| 10 | `Contact` | `contact` | `FIELDS` const |
| — | `Footer` | — | `NAV`, `SOCIAL` consts |

Supporting: `MediaLightbox` (portal modal), `Magnetic`, and four primitives
(`MaskText`, `RevealImage`, `EdgeTitle`, `FloatField`).

**Navigation is anchor-based.** `Header` holds seven ids, drives an
`IntersectionObserver` scroll-spy, and `globals.css` sets `scroll-margin-top`
tuned to the nav height. The nav is coupled to the page, not a link list.

**`src/lib/work.js` is the only content module already extracted** from a
component. It exists because `Portfolio` and `Hero` both need the film data.
It is the template for how the rest should be shaped, and the natural seam for
the API.

---

## 3. Existing backend architecture

None. This section exists only to record that.

---

## 4. Existing content and data sources

Traced end to end. Every row is a hardcoded array; nothing is fetched.

| Content | Lives in | Shape today | Count |
|---|---|---|---|
| Services | `Services.jsx` `SERVICES` | `{n, id, title, short, body, image, tags[]}` | 3 |
| Extra disciplines | `Services.jsx` `MORE` | plain strings | 6 |
| Portfolio tiles | `lib/work.js` `WORK` | `{id, name, meta, img, span, media[]}` | 8 |
| Portfolio films | same, `media[]` | `{type:'video', id, title}` | 6 across 5 tiles |
| Portfolio stills | same, `media[]` | `{type:'image', src, alt}` | 7 across 3 tiles |
| Team | `Team.jsx` `FOUNDERS` | `{id, first, last, role, lines[], image, social[]}` | 2 |
| Person socials | same, `social[]` | `{icon, label, href}` | 4 |
| Clients | `Clients.jsx` `CLIENTS` | `{id, name, sector, logo, href}` | 8 |
| Testimonials | `Testimonials.jsx` `QUOTES` | `{id, quote, name, role, image}` | 2 |
| Company socials | `Header.jsx` + `Footer.jsx` `SOCIAL` | `{icon, label, href}` | 4 and 5 — **they differ** |
| Contact fields | `Contact.jsx` `FIELDS` | name, email, phone, city, country, message | 6 |
| Stats | `About.jsx` `STATS` + `WhyChoose.jsx` | `{value, label}` | "5+" and "9" repeat in 5 places |
| About heading | `About.jsx` JSX | 3 `MaskText` segments, middle one `<em>` | 1 |
| About description | `About.jsx` JSX | paragraph | 1 |
| About figure | `About.jsx` JSX | `/media/INTERVIEW.webp` 900x900 | 1 |
| About caption | `About.jsx` JSX | "Visual Excellence, Tangible Results" — **also in the nav** | 1 |
| Hero collage | `Hero.jsx` `SHEET` | `{id, slot, img, alt}` | 4 |
| Ticker | `WhatWeOffer.jsx` `DISCIPLINES` | plain strings | 9 |

**Contact submissions go nowhere.** `Contact.jsx:19-24`:

```js
async function deliver(payload) {
  console.info('[Media Nest] contact submission (not yet transmitted):', payload)
  await new Promise((resolve) => setTimeout(resolve, 900))
  return { ok: true }
}
```

The form validates for real, shows a success animation, and discards the data.
The file's own header comment names `deliver()` as the single integration seam.

**Purely visual, no data source:** the 240-frame camera intro, all primitives,
`FloatField` bands, `EdgeTitle`, the marquee, the lightbox chrome.

---

## 5. Static vs dynamic boundary

`BACKEND-PLAN.md` §2–§4 defines this and it holds up against the code. Three
items need the reason recorded, because each looks editable and is not:

- **Navbar** — ids must match sections that exist; the scroll-spy observes
  those exact nodes. An editable nav can point at `#nothing` and break
  silently, with no validation possible server-side.
- **WhyChoose** — the scroll choreography assigns each of 4 reasons a progress
  range. A fifth row breaks the timing.
- **`Discipline.span`** — derived from the cover image's real pixel dimensions
  so nothing upscales. Must be **computed on save**, never an admin field.

### The boundary risk the plan does not cover

All content today is **synchronous at first paint**. The site has **29
`whileInView` reveals** across the exact sections that become CMS-driven:

```
Team 8 · Clients 5 · About 4 · Portfolio 3 · Contact 2 · others 1 each
```

Framer Motion's `whileInView` fires on intersection. If content arrives after
mount, three things break that no amount of careful API design fixes:

1. Sections render empty, get measured at the wrong height, and the reveal
   fires against a collapsed box.
2. A reader who scrolls fast passes a section before its data lands; the
   reveal has already been consumed, so the content appears with no animation.
3. Layout shift as arrays fill.

This is the single largest regression risk in the project, and it is why
Decision Gate 1 is the first thing to settle.

---

## 6. Backend-plan compliance analysis

| `BACKEND-PLAN.md` says | Verdict |
|---|---|
| 6 things editable + settings | **Confirmed.** Matches the content inventory in §4 |
| ~85% stays in code | **Confirmed.** ~6,300 characters of text total; most of the repo is motion and layout |
| 10 tables | **Confirmed**, with field-level notes in §9 |
| Store only the YouTube id, never files | **Confirmed.** 6 ids, all live on Media NEST TV |
| A tile has films **or** stills, never both | **Confirmed** against `work.js` — 5 video tiles, 3 image tiles, no overlap |
| 2 endpoints are enough | **Confirmed by the code.** No search, no filters, no auth, no pagination anywhere |
| Build order: Contact → Content → Settings | **Confirmed.** Contact is the only data currently being lost |
| Contact form has 6 fields | **Confirmed** at `Contact.jsx` `FIELDS` |
| Phone in 3 files, "5+" in 5 | **Confirmed** |

The plan is accurate. No requirement in it is unsupported by the code.

---

## 7. Conflicts between plan and brief

Resolved per the stated priority (working code → `BACKEND-PLAN.md` → brief).

**C1 — API surface.** Brief lists 9 endpoints including
`/api/disciplines/<id>/videos/` and `/api/disciplines/<id>/images/`.
`BACKEND-PLAN.md` specifies 2. The frontend renders every section on one page
in one paint, so per-discipline endpoints would be N+1 requests for data that
is always needed together. **Not silently resolved — Decision Gate 2.**

**C2 — Slugs.** Brief asks to validate slugs. There are no detail pages and no
routes; the lightbox is in-page. A slug would be a column nothing reads.
**Decision Gate 4.**

**C3 — P0/P1/P2.** Brief cites a priority scheme not present in the source
document. Mapped onto the plan's 3-step order in §19 rather than invented.

**C4 — S3/object storage.** Brief asks to evaluate it. The plan does not
mention it. It becomes relevant only because of where Django will be hosted —
**Decision Gate 3.**

**C5 — Header and Footer social lists differ** (4 vs 5 links; Footer adds
WhatsApp). Not a plan/code conflict, but it must be decided before one
`SocialLink` table replaces both, or one surface silently changes.

---

## 8. Final Django architecture

```
medianest-backend/
  manage.py
  requirements.txt
  config/
    settings/  base.py · dev.py · prod.py
    urls.py
    wsgi.py
  content/            # one app, all ten models
    models.py
    admin.py
    serializers.py
    views.py
    urls.py
    migrations/
    management/commands/seed_content.py
  enquiries/          # kept separate: different access rules, different retention
    models.py
    admin.py
    serializers.py
    views.py
```

**Two apps, not ten.** `content` is read-only public data with identical
handling. `enquiries` is write-from-public, read-in-admin, holds personal data,
and will have its own retention and export rules. That is a real boundary.
Everything else would be ceremony.

**Dependencies:** `django`, `djangorestframework`, `django-cors-headers`,
`Pillow`, `psycopg[binary]`, `python-dotenv`. Nothing else without a gate.

---

## 9. Database models and relationships

```
SiteSettings (singleton)
Service
Discipline ──< DisciplineVideo
           └─< DisciplineImage
TeamMember ──< SocialLink >── (null owner = company link)
Client
Testimonial
ContactEnquiry
```

Every model carries `order` (`PositiveIntegerField`, `db_index=True`) and
`is_published` / `is_active` (`BooleanField(default=True, db_index=True)`),
plus `created_at` / `updated_at`. `Meta.ordering = ['order', 'id']`.

### Field-level notes

**`Service`** — `title`, `short_label`, `body` (TextField), `image`
(ImageField), `tags` (see Gate 6), `is_featured`.
`is_featured=True` → one of the three detailed cards; `False` → appears in the
`MORE` name list. One model covers both lists.
**Do not store the `01/02/03` number** — it is array position. Compute it.

**`Discipline`** — `name`, `meta_label`, `cover` (ImageField),
`span_cols`/`span_rows` (PositiveSmallInteger, **computed in `save()`** from
`cover.width/height`, `editable=False`).

**`DisciplineVideo`** — `discipline` (FK, `on_delete=CASCADE`, `related_name='videos'`),
`youtube_id` (CharField(20)), `title`, `order`.
Validate `youtube_id` against `^[A-Za-z0-9_-]{11}$` — the current data includes
one field on the old site where two URLs were pasted into one box, which is
exactly the mistake this prevents.

**`DisciplineImage`** — `discipline` (FK, CASCADE, `related_name='images'`),
`image`, `alt` (**required**, not blank — the frontend passes it to `<img alt>`),
`order`.

**`TeamMember`** — `first_name`, `last_name`, `role`, `descriptor_lines`
(see Gate 6), `photo`, `is_active`.

**`SocialLink`** — `platform` (choices: instagram / youtube / linkedin /
facebook / whatsapp), `url`, `order`, `member` (FK to TeamMember,
`null=True, blank=True`, `on_delete=CASCADE`, `related_name='socials'`).
`member=NULL` means a company link.
**Store `platform`, never the Font Awesome class.** The frontend maps platform
→ icon. An admin typing `fab fa-instagram` is an admin editing CSS.

**`Client`** — `name`, `sector`, `logo`, `url` (URLField, blank allowed).

**`Testimonial`** — `quote` (TextField), `person_name`, `person_role`, `photo`.

**`ContactEnquiry`** — `name`, `email`, `phone`, `city` (blank), `country`
(blank), `message`, `status` (new/replied/closed, default new, indexed),
`created_at` (indexed), `ip_address` (GenericIPAddressField, null), `user_agent`
(TextField, blank), `internal_notes` (TextField, blank).
**No `updated_at` on the enquiry body** — only `status` and `internal_notes`
should ever change; see §10.

**`SiteSettings`** — `email`, `phone`, `whatsapp_url`, `years_of_practice`
(CharField, not Integer — the value rendered is `"5+"`), `discipline_count`
(CharField, same reason), `working_hours`, `operational_scope`, `company_blurb`,
`meta_description`, `showreel_youtube_id` (blank).
Enforce a single row by overriding `save()` with `pk=1`.

### Deliberately absent

`slug` (no routes) · `Category` (the 8 tiles *are* the taxonomy; nothing
filters) · `Project` (no client-project entity exists) · `Video` model (a
YouTube id on a child row is enough) · `NavItem` · `Page`/`Block` ·
`published_at` scheduling · soft-delete · versioning.

---

## 10. Django Admin architecture

Plain `ModelAdmin`. No custom CMS UI.

| Admin | Config |
|---|---|
| `SiteSettings` | `has_add_permission=False`, `has_delete_permission=False`. Redirect changelist → the single object |
| `Service` | `list_display` title / featured / order / published, `list_editable` order+published, thumbnail preview |
| `Discipline` | Two inlines: `DisciplineVideoInline`, `DisciplineImageInline` (both `TabularInline`, `extra=0`). `span_*` shown read-only with a note that it is computed |
| `TeamMember` | `SocialLinkInline` filtered to that member |
| `SocialLink` | Own changelist for company links (`member__isnull=True`) |
| `Client`, `Testimonial` | thumbnail, order, published |
| `ContactEnquiry` | **`has_add_permission=False`.** All body fields `readonly_fields`; only `status` and `internal_notes` editable. `list_filter` status + created_at, `search_fields` name/email/phone/message, `date_hierarchy`, CSV export action |

Enquiries are evidence. An admin who can silently edit the message body
destroys the only record of what someone actually sent.

**Ordering UX:** integer `order` with `list_editable` is enough at these counts
(3, 8, 2, 8, 2). Drag-and-drop reordering is a dependency for a problem that
does not exist here.

---

## 11. API contract

Per `BACKEND-PLAN.md`, pending Decision Gate 2.

### `GET /api/content/`

Returns every published content object in one document. No auth. No pagination.

```
200  { "settings": {...}, "services": [...], "disciplines": [...],
       "team": [...], "clients": [...], "testimonials": [...],
       "company_socials": [...], "generated_at": "<iso8601>" }
```

- Only `is_published` / `is_active` rows. Ordering applied server-side by
  `order, id`; the client never sorts.
- Nested: `disciplines[].videos[]`, `disciplines[].images[]`,
  `team[].socials[]`. Use `prefetch_related` — four queries total, not N+1.
- **Empty collections return `[]`, never `null`.** The frontend maps over them.
- Image fields return absolute URLs.
- `ETag` + `Last-Modified` from the newest `updated_at` across all models.
  `304` on match. `Cache-Control: public, max-age=60`.
- `500` returns a JSON error body, never Django's HTML debug page in prod.

### `POST /api/contact/`

```
201  { "ok": true, "id": <int> }
400  { "errors": { "email": ["Enter a valid email address."], ... } }
429  { "detail": "Too many submissions. Please try again later." }
```

- Body: `name`, `email`, `phone` required; `city`, `country` optional;
  `message` required. Field names match `Contact.jsx` `FIELDS` exactly.
- Validation mirrors the frontend: email regex, phone ≥ 7 digits after
  stripping non-digits, message non-empty. Server-side is authoritative.
- Rate limit by IP: 5/hour. Honeypot field. See §14.
- Sends notification email on success; **a mail failure must not fail the
  request** — the row is already saved, and losing the enquiry is worse than a
  missing email.

### CORS

`django-cors-headers`, `CORS_ALLOWED_ORIGINS` explicit — the Vercel production
domain, any preview domain pattern, and `http://localhost:5173`.
Never `CORS_ALLOW_ALL_ORIGINS`. `POST /api/contact/` needs no credentials, so
`CORS_ALLOW_CREDENTIALS = False`.

---

## 12. Frontend integration map

Exact files. **Data source only — no markup, layout, style or motion changes.**

| File | Change |
|---|---|
| `src/lib/work.js` | `WORK` and `SHOWREEL` sourced from content instead of literals. Keep the module and both export names — `Portfolio` and `Hero` import them and must not change |
| `src/lib/content.js` *(new)* | The single content accessor. Every section imports from here |
| `src/components/Services.jsx` | `SERVICES`, `MORE` ← content |
| `src/components/Team.jsx` | `FOUNDERS` ← content; map `platform` → icon class here |
| `src/components/Clients.jsx` | `CLIENTS` ← content |
| `src/components/Testimonials.jsx` | `QUOTES` ← content |
| `src/components/WhatWeOffer.jsx` | `DISCIPLINES` ← derived from service titles, not a second list |
| `src/components/About.jsx` | Heading, description, figure + caption, the 3 pillars' text, and the 4 stat values ← content. Pillar **count**, numbers, eyebrow, EdgeTitle and the grid stay in code |
| `src/components/WhyChoose.jsx` | `stat` values ← settings; the 4 reasons stay in code |
| `src/components/Contact.jsx` | **`deliver()` body only** (lines 19-24). Everything else in that file is untouched |
| `src/components/Header.jsx` | `SOCIAL` ← content. `NAV` stays in code |
| `src/components/Footer.jsx` | `SOCIAL` ← content; email and phone ← settings. `NAV` stays in code |
| `src/components/Portfolio.jsx` | **No change.** It already reads `WORK` from `lib/work.js` |
| `src/components/Hero.jsx` | **No change.** Home is static by decision — see the section scope below |

**Never touched:** `MediaNestIntro.jsx`, `MediaLightbox.jsx`, `Magnetic.jsx`,
all four primitives, every `.css` file, `App.jsx` section order, `main.jsx`.

**Also to fix, unrelated to the backend:** `Testimonials.jsx:65` still carries
`id="video"`, a leftover from the removed nav item. Nothing points at it.

---

## 12a. Section scope, as decided

Walked section by section against the rendered page and the measured geometry,
rather than inferred from the component source. Decisions taken so far:

### Home — **static, no change**

Decided: leave it exactly as it is. No `HeroImage` model, no `Hero.jsx` edit.

It was the riskiest section to make dynamic anyway. Every other section
reveals on `whileInView`; the Hero animates on **mount**, with staggered
delays (headline words at 0.075s steps, the four collage frames at 0.12s
steps with a `clipPath` reveal). Late content would animate empty boxes above
the fold. Its headline is also split per word into individual masks, so a
longer line breaks the three-line composition silently.

**One consequence to accept:** `5+` and "Nine disciplines" appear in *both*
Hero and About. About will read them from `SiteSettings`; Hero will not.
Editing the figure in admin will change About and leave Hero at the old value —
two different numbers on one page. Either accept that and remember to edit
`Hero.jsx` too, or make that one value in Hero read from settings, which is a
one-line change touching no markup, style or motion. **Open.**

### About — dynamic, with the count fixed

| Atom | Decision | Note |
|---|---|---|
| Heading | **Dynamic** | Stored as text with `*seen*` marking the `<em>`. Safe because this heading is three `MaskText` segments that flow and wrap, not the Hero's per-word split |
| Description | **Dynamic** | Plain paragraph |
| Figure image | **Dynamic** | Box measures 433x458 (ratio 0.95), `object-fit: cover`. Minimum upload **866 x 916** for 2x. Current source is 900x900 and only just clears it |
| Figure `focal_x/y` | **Dynamic** | `object-position` is centred here, not hand-tuned as in the Hero, but a near-square crop still needs a focal point when a face sits off-centre |
| Figure caption | **Settings** | "Visual Excellence, Tangible Results" is also the nav tagline — one source |
| 3 pillars: title, body | **Dynamic** | |
| 3 pillars: **count** | **Fixed at 3** | Add and delete disabled in admin |
| Pillar numbers `01/02/03` | Computed | Array position, never stored |
| 4 stat values | **Settings** | All four repeat elsewhere: `5+` in 5 places, `9` in 4, `24/7` and `Global` in Contact and Footer |
| 4 stat labels | Static | Copy, not data |
| Stat count | **Fixed at 4** | `grid-template-columns: repeat(4, 1fr)` |
| Eyebrow, EdgeTitle | Static | |

**Why the counts are fixed.** The bento is a 12-column grid and the figure
occupies 4 columns across 2 rows, so the pillars have to tile what is left:

```
Row 1:  [figure 4] [pillar 4] [pillar 4]      = 12
Row 2:  [figure  ] [pillar 8 wide      ]      = 12
```

Measured: 433 · 433 · 881. Three is not an arbitrary number — it is what
fills the grid. Counts that tile without holes are 3, 4, 7, 8, 10, 11; five,
six and nine leave empty cells. Rather than give an admin that arithmetic, the
count is fixed and only the text is editable. The stats row is hardcoded to
four columns for the same reason.

**This revises an earlier call in this document.** §5 and §12 previously said
the About pillars stay in code. Measuring the grid showed that only the
*count* is load-bearing; the text is free to change.

---

## 13. Media and storage architecture

### Stays in the repo — never CMS

`public/sequence/` (240 frames, 3.5MB) · `public/images/` logo and favicon ·
Hero collage (4 images chosen for specific crop behaviour) · every decorative
SVG. These are implementation, not content.

### Becomes CMS media

Service images (3) · Discipline covers (8) · Gallery images (7) · Team photos
(2) · Client logos (8) · Testimonial photos (2) · About figure (1).
**31 files, ~2MB today.**

The Hero's four collage images are **not** in this list: Home is static by
decision (see the section scope below), so they stay in the repo. An earlier
version of this document said 30 files and had omitted the About figure and
the Hero collage entirely.

### Handling

- `ImageField` with `upload_to='services/%Y/%m/'` etc.
- Validate on upload: extension allowlist, max 5MB, max 4000px.
- **Store width/height on save** — `Discipline.span_*` depends on it.
- Generate a WebP derivative with Pillow; the site is already all-WebP.
- `alt` required on `DisciplineImage`; derived from `name` elsewhere.
- Deleting a row must not orphan the file — delete on `post_delete`.

### Video

YouTube ids only. Never `FileField` for video. Already decided and already
true in `work.js`.

---

## 14. Contact-form architecture

**Current:** `Contact.jsx` holds `values` in `useState`, `validate()` checks
required/email/phone/message, `onSubmit` awaits `deliver()`, `status` drives an
idle → sending → done state machine with a spark burst and a check mark.

**Change:** the body of `deliver()`. Nothing else.

```
deliver(payload)  ->  POST {API}/api/contact/
                      201 -> return { ok: true }
                      400 -> surface field errors into the existing `errors` state
                      5xx/network -> show the existing error line, keep values
```

The existing UI already has an error surface (`mn-form__status`) and per-field
error rendering, so failure states need no new markup.

**Spam protection, in order of cost:**

1. **Honeypot** — a hidden field real users never fill. One input, zero deps.
2. **Time trap** — reject submissions faster than ~3 seconds from mount.
3. **IP rate limit** — 5/hour, DRF throttle.

That is enough for a firm receiving a handful of enquiries. **CAPTCHA is not
recommended**: it adds a third-party script to a site whose whole design
argument is restraint, and it hurts conversion on the one form that matters.
Revisit only if spam actually arrives.

---

## 15. Security and validation

- `DEBUG=False` in prod; `SECRET_KEY`, `DATABASE_URL`, `ALLOWED_HOSTS` from env.
- Django admin behind HTTPS with a non-default URL path; staff accounts only,
  no public registration, no public write API except contact.
- `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, HSTS.
- Serializers are read-only for content; `ContactEnquirySerializer` accepts
  exactly six fields and ignores anything else in the body.
- Strip/limit message length (e.g. 5000 chars) before save.
- `ip_address` and `user_agent` stored for abuse triage only. They are personal
  data — agree a retention period (suggest: purge enquiries older than 24
  months) rather than keeping them forever by default.

---

## 16. Performance and caching

The whole payload is ~6,300 characters of text plus image URLs — a few KB
gzipped. The performance question is not query speed, it is request count.

- One `/api/content/` call, `prefetch_related` on the two nested sets.
- `ETag`/`304` so repeat visits transfer nothing.
- Invalidate on save via `post_save`/`post_delete` signals bumping a cache key.
- **No CDN needed for the API.** Media should sit behind one — see Gate 3.
- Django's own `ConditionalGetMiddleware` covers most of this.

---

## 17. Testing strategy

| Layer | What |
|---|---|
| Models | `span_*` computed correctly from cover dimensions; `SiteSettings` stays a single row; `youtube_id` regex rejects the double-URL case |
| API | `/api/content/` shape and ordering; unpublished rows excluded; empty sets serialize `[]`; `304` on ETag |
| Contact | valid 201 + row created; each invalid field → 400 with that field named; honeypot → silent 201 with no row; throttle → 429; mail failure still returns 201 |
| Admin | enquiry body read-only; add disabled on enquiries and settings |
| **Parity** | **The critical one.** Snapshot the current rendered DOM for all 11 sections, seed the database from the existing constants, re-render, diff. Must be identical |
| Regression | Puppeteer: intro completes; all 8 tiles open; lightbox pages and closes with focus return; contact submits; 6 viewports show no overlap or horizontal scroll; no console errors |

The repo already has Puppeteer as a devDependency and this session's regression
scripts to adapt.

---

## 18. Phase dependencies

```
  Phase 0  Django skeleton + deploy target
     |
     +-----------------------------+
     |                             |
  Phase 1  Contact               Phase 2  Content models + seed
  (independent, ships alone)       |
                                 Phase 3  /api/content/ + frontend swap
                                   |
                                 Phase 4  Settings de-duplication
                                   |
                                 Phase 5  Hardening
```

Phase 1 depends on nothing but Phase 0 and can ship the same day. Phase 3 is
the only phase that touches rendering.

---

## 19. Phase-by-phase execution plan

Mapped from `BACKEND-PLAN.md`'s 3-step order; the brief's P0/P1/P2 labels are
noted where they correspond.

### Phase 0 — Skeleton *(prerequisite, not in the source plan)* — **BUILT**

**Objective:** a Django project that boots, with a decided deploy target.
**Existing:** built and verified. `config/settings/{base,dev,prod}.py`,
`core` health endpoint, whitenoise, gunicorn, `railway.json`, `Procfile`.
Verified: `check` clean, `migrate` applied, `/api/health/` 200 with a real
database round trip, `/admin/login/` 200 with `DEBUG=False`, fingerprinted
admin CSS served by whitenoise (24,733 bytes), prod settings refuse to boot
without `DJANGO_SECRET_KEY` / `DJANGO_ALLOWED_HOSTS` / `CORS_ALLOWED_ORIGINS`.
**Not verified:** the gunicorn start command. gunicorn cannot run on Windows
(`fcntl`), so it is correct-by-construction for Railway's Linux but untested
locally. First deploy is the test.
**Was:** nothing.
**Changes:** project scaffold, settings split, env loading, CORS, DRF, admin
superuser, health endpoint.
**DB:** initial Django migrations only.
**Blocked by:** Decision Gates 1 and 3.
**DoD:** admin reachable over HTTPS on the chosen host; `/api/health/` 200.
**Rollback:** delete the backend; frontend is untouched and unaffected.

### Phase 1 — Contact enquiries *(brief: P0)*

**Objective:** stop losing enquiries.
**Existing:** `Contact.jsx` `deliver()` discards the payload.
**Changes:** `enquiries` app, `ContactEnquiry` model, serializer, throttled
`POST /api/contact/`, honeypot + time trap, admin with read-only body and CSV
export, notification email.
**Frontend:** body of `deliver()` only. One hidden honeypot input.
**Migrations:** `enquiries/0001_initial`.
**Testing:** the Contact row of §17, plus a live end-to-end submission.
**Acceptance:** a real submission appears in admin within seconds; an invalid
email is rejected with the existing inline error; mail failure still persists.
**DoD:** above, and the old console-log path removed.
**Rollback:** revert `deliver()` to the stub. Backend can stay up harmlessly.

### Phase 2 — Content models and seed *(brief: P0/P1)*

**Objective:** the database can express everything the site shows today.
**Changes:** all nine content models, admin, `seed_content` management command
reading the existing constants verbatim.
**Migrations:** `content/0001_initial`.
**Acceptance:** `python manage.py seed_content` produces 3 services, 8
disciplines, 6 videos, 7 images, 2 team, 4+5 socials, 8 clients, 2
testimonials, 1 settings row — matching §4 exactly.
**DoD:** an admin can add a client end to end. **No frontend change yet.**
**Rollback:** drop the app; nothing consumes it.

### Phase 3 — API and frontend swap *(brief: P0/P1)*

**Objective:** the site renders from the database with no visible difference.
**Changes:** `/api/content/`, `src/lib/content.js`, the swaps in §12.
**Blocked by:** Decision Gate 1 — this phase's shape depends entirely on it.
**Testing:** the **parity test** is the gate. Section-by-section DOM diff
against the pre-change snapshot, plus the full Puppeteer regression.
**Acceptance:** rendered output identical; no new layout shift; all 29
`whileInView` reveals still fire; intro and lightbox untouched.
**DoD:** parity clean on desktop, tablet and phone widths.
**Rollback:** `src/lib/content.js` falls back to the bundled constants behind
one flag. Keep the constants in the repo until Phase 5 proves the API stable.

### Phase 4 — Settings de-duplication *(brief: P1)*

**Objective:** one source for contact details and the repeated figures.
**Changes:** `Header`, `Footer`, `Contact`, `About`, `WhyChoose`, `Hero` read
settings. Resolve C5 (Header vs Footer social lists) first.
**Acceptance:** changing the phone number in admin changes all three places.
**Rollback:** per-file revert; each is independent.

### Phase 5 — Hardening *(brief: P2)*

Caching headers and invalidation, image derivatives and validation, enquiry
retention policy, backups, monitoring, removal of the fallback constants.

---

## 20. Decision gates

**Gate 1 — How content reaches the browser**

- **Context:** the site is a client-rendered SPA with 29 scroll-triggered
  reveals and already ships an almost-empty HTML shell to crawlers. Moving
  content behind a runtime fetch makes both worse.
- **Option A — Build-time fetch.** Vite pulls `/api/content/` during
  `vite build` and bakes it into the bundle. A publish in Django fires a
  webhook that triggers a Vercel rebuild.
  *Site stays fully static. Zero loading states. Zero animation risk. SEO
  unchanged or better. Content goes live in ~1–2 minutes.*
- **Option B — Runtime fetch.** The SPA calls the API on mount.
  *Instant updates. Requires loading/skeleton states, reintroduces layout
  shift, puts the 29 reveals at risk, and makes the SEO problem worse.*
- **Recommended: A.** Nothing on this site needs sub-minute publishing, and A
  is the only option that keeps the promise that the UI does not change.
- **Impact:** decides Phase 3 entirely, and whether Phase 0 needs a webhook.

**Gate 2 — API surface**

- **Context:** the brief lists 9 endpoints; `BACKEND-PLAN.md` specifies 2.
- **Option A — 2 endpoints** (`GET /api/content/`, `POST /api/contact/`).
- **Option B — 9 REST endpoints** as the brief lists.
- **Recommended: A.** Everything renders in one paint; B is 7 extra round
  trips for data always needed together, and per-discipline video/image
  endpoints are N+1 by construction. B also conflicts with Gate 1 Option A.
- **Impact:** serializer and view structure; ~1 day of work difference.

**Gate 3 — Where Django and media live**

- **Context:** Vercel hosts static output; it cannot run Django. No hosting
  exists today and the plan does not cover it.
- **Option A — Managed PaaS** (Railway / Render / Fly) with Postgres and local
  `MEDIA_ROOT` on a persistent volume. *Simplest; media limited to one host.*
- **Option B — PaaS + S3-compatible object storage** (`django-storages`).
  *Media on a CDN, survives host migration, ~$1/month at this size.*
- **Recommended: B**, because media is the one thing that must outlive the
  backend host, and 31 files today becomes hundreds once galleries grow.
- **Impact:** Phase 0 settings; whether `Pillow` writes locally or to a bucket.

**Gate 4 — Slugs and detail pages**

- **Context:** the brief asks about slugs; no routes or detail pages exist.
- **Option A — No slug.** Matches the current UI.
- **Option B — Add `slug`** now, unused, in case detail pages come later.
- **Recommended: A.** `src/future/` already holds a parked multi-page scaffold
  if that direction is ever taken; a slug column read by nothing until then is
  a field that will drift out of sync.
- **Impact:** one field per content model.

**Gate 5 — Database in Phase 0**

- **Option A — SQLite** for Phases 0–2, Postgres from Phase 3.
- **Option B — Postgres from the start.**
- **Recommended: B.** The gap between them is one connection string, and
  discovering a Postgres-only problem during the parity test in Phase 3 is the
  worst time to find it.

**Gate 6 — `tags` and `descriptor_lines` storage**

- **Context:** `Service.tags` (4 short strings) and `TeamMember.descriptor_lines`
  (2–3 lines) are ordered string lists.
- **Option A — Postgres `ArrayField`.** One column, simple admin.
- **Option B — Child tables.** Ordering and reuse, five more clicks per edit.
- **Recommended: A.** Nothing filters, searches or joins on these.
- **Impact:** couples those two models to Postgres, which Gate 5 B already
  assumes.

---

## 21. Risks

| Risk | Severity | Mitigation |
|---|---|---|
| Async content breaks the 29 scroll reveals | **High** | Gate 1 Option A removes it entirely |
| Parity drift — the site looks subtly different after Phase 3 | **High** | Seed from the existing constants verbatim; DOM-diff parity test is the phase gate |
| `span` typed by an admin breaks the portfolio grid | Medium | `editable=False`, computed in `save()` |
| Backend down → site has no content | Medium | Gate 1 A makes the site immune; under B, keep the bundled fallback |
| Media lost on host migration | Medium | Gate 3 B |
| Enquiry spam | Medium | Honeypot + time trap + throttle; CAPTCHA only if it actually arrives |
| Header/Footer social lists silently unified | Low | Resolve C5 before Phase 4 |
| Enquiries held indefinitely with IP and user agent | Low | Agreed retention policy in Phase 5 |

---

## 22. Definition of Done

**Per phase:** the acceptance criteria in §19, migrations committed and
reversible, tests for that phase green, no console errors, rollback verified.

**Whole project:**

- [ ] Every enquiry since launch is in the database and none were lost
- [ ] An admin can add a service, client, testimonial, team member and
      portfolio film without a developer or a deploy from a developer
- [ ] Changing the phone number in admin changes it in all three places
- [ ] The rendered site is **visually identical** to commit `e7ae6e6` —
      verified by DOM diff at three widths
- [ ] The camera intro, lightbox, scroll reveals and nav scroll-spy behave
      exactly as before
- [ ] `/api/content/` returns `304` for an unchanged payload
- [ ] `DEBUG=False`, secrets in env, CORS restricted to known origins
- [ ] Media survives a backend redeploy
- [ ] The bundled fallback constants are removed only after the API has been
      stable in production

---

## Notes

- `BACKEND-PLAN.md` is gitignored. If this plan is to be handed to a backend
  developer, both documents need to be committed or shared deliberately.
- `src/future/` (188 files, `react-router-dom`) stays parked by decision. It is
  the relevant prior art if Gate 4 is ever revisited.
- Two frontend items are independent of this work: the expired SSL certificate
  on medianest.co.in, and the stale `id="video"` on `Testimonials.jsx`.
