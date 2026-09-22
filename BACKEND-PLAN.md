# MediaNest -- Backend Plan

What should be editable from an admin panel, what should stay in code, and
what needs to be built.

---

## 1. The short answer

The website does **not** need to become database-driven.

Right now every piece of text and every image is written directly into the
code. That is fine for most of it. Only the parts that **keep changing** are
worth moving into Django.

- About **85%** stays exactly as it is -- design, layout, animation, headings.
- About **15%** moves to Django -- the lists of business records.

**6 things become editable. 1 thing gets saved. Everything else stays in code.**

How big this site actually is:

| | Count |
|---|---|
| Pages | 1 (everything is one scrolling page) |
| Services | 3 |
| Portfolio tiles | 8 (5 with a film, 3 with photos) |
| Films (YouTube) | 6 |
| Gallery photos | 7 |
| Team members | 2 |
| Client logos | 8 |
| Testimonials | 2 |
| Contact form fields | 6 |
| All the text on the site | ~6,300 characters |

That last row is the important one. This is a **small content site**. A big
CMS would be more work to maintain than the site itself.

---

## 2. What becomes editable

| Section | What the admin can do | Why it is worth it |
|---|---|---|
| **Contact form** | Read every enquiry, mark it New / Replied / Closed | **Enquiries are being thrown away today.** The form validates and says thank you, but sends nothing anywhere. |
| **Services** | Add, edit, reorder, hide. Change text and photo | The service list grows, and wording changes for sales reasons |
| **Portfolio** | Change the 8 tiles, swap covers, manage films and photos | This is the firm's visual proof. New work keeps arriving |
| **Team** | Add or remove a person, change name, role, photo, social links | People and job titles change |
| **Clients** | Add a logo, reorder, hide | Winning a client should not need a developer |
| **Testimonials** | Add, edit, hide | Only 2 exist. They will keep coming |
| **Site settings** | Email, phone, WhatsApp, social links, "5+ years", "9 disciplines", working hours | See below |

**Why settings matter:** the phone number is written into **3 different files**
today, and "5+ years" into **5**. One edit should fix all of them. And "5+
years" quietly becomes wrong every year.


## 3. How it will work

### Content

```
   Admin logs into Django Admin
              |
   Adds / edits / reorders / hides an item
              |
         Saved in database
              |
   Website asks once on load:  GET /api/content/
              |
   React shows it with the SAME design and animation as now
```

The design never changes. Only the words and images inside it change.

### Contact form

```
   Visitor fills the form
              |
        POST /api/contact/
              |
   Saved in database  +  email sent to MediaNest
              |
   Admin opens Django Admin and sees it
              |
   Marks it:  New  ->  Replied  ->  Closed
```

Two endpoints are enough. The site has no search, no filters and no login, so
there is no reason to split the content into seven separate API calls.

---

## 4. Section by section

| Section | Editable? | Admin manages | Code keeps |
|---|---|---|---|
| Camera intro | No | -- | Everything |
| Hero | Mostly no | The description paragraph only | Headline, images, buttons |
| About | Partly | The numbers (5+, 9) | The 3 pillars, layout |
| Scrolling words | Automatic | -- | Comes from Services by itself |
| **Services** | **Yes** | Title, text, photo, tags, order, show/hide | Layout, numbering, animation |
| **Portfolio** | **Yes** | Tile name, label, cover, films, photos, order | Grid, tile sizes, lightbox |
| Why Choose Us | No | The numbers only | All 4 points |
| **Team** | **Yes** | Name, role, description lines, photo, socials, order | Layout, decoration |
| **Clients** | **Yes** | Name, sector, logo, website, order | Grid, styling |
| **Testimonials** | **Yes** | Quote, name, role, photo, order, show/hide | Slider, animation |
| **Contact** | **Yes** | Enquiries + contact details | Form design, validation, animation |
| Navbar | No | -- | Everything |
| Footer | Partly | Email, phone, social links | Layout, wordmark |

---

## 5. What gets built

**10 tables:**

| Table | What it stores |
|---|---|
| `SiteSettings` | Email, phone, socials, the numbers, working hours (one row only) |
| `Service` | The service list |
| `Discipline` | The 8 portfolio tiles |
| `DisciplineVideo` | The YouTube id and title for a tile's film |
| `DisciplineImage` | Photos inside a tile's gallery |
| `TeamMember` | Founders and staff |
| `SocialLink` | Social links, for the company and per person |
| `Client` | Client logos |
| `Testimonial` | Quotes |
| `ContactEnquiry` | Form submissions (name, email, phone, city, country, message) |

Two rules for the portfolio tables:

- Store **only the YouTube id**, never a video file. YouTube does the hosting,
  the bandwidth and the transcoding for free.
- A tile has **either** films **or** photos, never both. Admin should not have
  to think about it -- let them add whichever they have, and the site picks the
  right viewer.

**Build in this order:**

1. **Contact form.** Save enquiries, send an email, show them in admin. This
   stops losing business today and is roughly a day of work.
2. **Content.** Services, Portfolio, Team, Clients, Testimonials. Load the
   current content in as starting data so the site looks identical on day one.
3. **Settings.** Email, phone, socials and the repeated numbers in one place.

**Not needed:** page builder, editable navigation, database-driven styling or
animation, categories, a separate Project model, self-hosted video, content
versioning, approval workflows, multiple languages.

---

## 6. Things to know before you start

### Three fixes Django will not make

1. **The old site's SSL certificate has expired.** medianest.co.in shows a
   security warning in every browser right now.
2. **Google sees an almost empty page.** The site draws all its text with
   JavaScript after loading, so the HTML that arrives is a blank shell. This
   gets worse as more text moves to the API. Worth planning for before launch.


### The portfolio photos are collages

The 7 gallery photos came from the old site, and each one is a **collage** --
six separate photographs saved together as a single image. That is how the old
site stored them.

They work and they look fine. But they cannot be re-cropped, they cannot have
individual captions, and on a phone the whole collage shrinks instead of
reflowing.

If the original individual photographs still exist, uploading them one by one
through the new admin would be a real improvement. Not urgent, but worth
knowing before someone assumes the gallery is already doing its best.
