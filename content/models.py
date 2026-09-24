"""
Content models.

Built section by section against the live frontend rather than all at once,
so every field here exists because something on the page renders it. See
IMPLEMENTATION PLAN.md section 12a for the decisions behind each one.

Built so far: Site settings, About.
"""

from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator, RegexValidator, URLValidator
from django.db import models


class Singleton(models.Model):
    """
    A table that holds exactly one row.

    `save()` pins the primary key rather than checking for existing rows,
    so two concurrent saves update the same row instead of racing to create
    a second one.
    """

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("This is a settings record and cannot be deleted.")

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class SiteSettings(Singleton):
    """
    Facts about the firm that more than one section states.

    Every field here was written out separately in several components. The
    numbers are `CharField`, not integers, because the page renders "5+" and
    "24/7" -- the plus sign and the slash are part of the value, not
    formatting applied to a number.

    Several facts are shown two ways and both spellings are deliberate: the
    hero writes "Nine disciplines" where the stats row writes "9", and the
    stats row writes "24/7" where the footer writes "24 x 7". Unifying them
    would be a visible change to a page that is not being redesigned, so both
    renderings are stored.
    """

    tagline = models.CharField(
        max_length=120,
        default="Visual Excellence, Tangible Results",
        help_text="Appears in the nav and on the About figure.",
    )

    years_of_practice = models.CharField(
        max_length=12,
        default="5+",
        help_text='As displayed, including the plus: "5+". Shown in the hero, About and Why Choose Us.',
    )
    discipline_count = models.CharField(
        max_length=12,
        default="9",
        help_text='The digit form: "9". Used in the About stats row.',
    )
    discipline_count_word = models.CharField(
        max_length=24,
        default="Nine",
        help_text='The word form: "Nine". The hero writes "Nine disciplines".',
    )
    hours_compact = models.CharField(
        max_length=16,
        default="24/7",
        help_text='Tight form for the stats row: "24/7".',
    )
    hours_spaced = models.CharField(
        max_length=16,
        default="24 x 7",
        help_text='Spaced form used in prose and the footer: "24 x 7".',
    )
    coverage = models.CharField(
        max_length=40,
        default="Global",
        help_text='Where the firm works: "Global".',
    )

    # How to reach the firm. These live here rather than in the Contact
    # section's own record because three components print them -- Contact, the
    # footer, and the header's mobile menu -- and the footer also builds a
    # WhatsApp link around the number. Kept in one place, changing the phone
    # is one edit; kept per section it was four, one of them URL-encoded
    # inside a link.
    firm_name = models.CharField(
        max_length=80,
        default="Media Nest",
        help_text="The legal or trading name, as the contact panel prints it.",
    )
    email = models.EmailField(
        default="connect@medianest.co.in",
        help_text="Shown and linked in the contact panel, the footer and the mobile menu.",
    )
    phone_display = models.CharField(
        max_length=32,
        default="+91-8448112770",
        help_text='As it should read on the page, punctuation and all: "+91-8448112770".',
    )
    phone_e164 = models.CharField(
        max_length=20,
        default="+918448112770",
        validators=[
            RegexValidator(
                r"^\+[1-9]\d{7,14}$",
                "Write it as a plus, the country code and the number, with no "
                "spaces or dashes: +918448112770.",
            )
        ],
        help_text=(
            "The dialable form. Both the tap-to-call link and the WhatsApp "
            "link are built from this, so it has to be the bare international "
            "number."
        ),
    )
    whatsapp_message = models.CharField(
        max_length=200,
        default="Hi, I visited your website and want to know more.",
        help_text="Pre-filled in the WhatsApp chat the footer icon opens.",
    )

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "site settings"
        verbose_name_plural = "site settings"

    def __str__(self):
        return "Site settings"


class AboutContent(Singleton):
    """
    The About section's own copy and figure. One row.

    The heading is stored as plain text with the accented word wrapped in
    asterisks -- `We shape the way a brand is *seen*, frame by frame.` The
    frontend splits on that and renders the middle part as the orange italic.
    Asterisks rather than HTML because an admin should not be writing markup,
    and this heading is three flowing segments, not a fixed composition: it
    wraps naturally, so a longer line is safe here in a way it is not in the
    hero.
    """

    heading = models.CharField(
        max_length=200,
        default="We shape the way a brand is *seen*, frame by frame.",
        help_text="Wrap one word or phrase in *asterisks* to set it in the orange italic.",
    )
    description = models.TextField(
        default=(
            "Media Nest is a brand image management and consultancy practice. "
            "We create and curate visual content that drives engagement, trust "
            "and lasting presence — from photography and cinematography through "
            "to strategy, events and digital."
        ),
        help_text="The paragraph to the right of the heading.",
    )

    figure = models.ImageField(
        upload_to="about/",
        blank=True,
        help_text=(
            "The large image beside the pillars. The frame is 433x458 on a "
            "desktop and crops to fill, so upload at least 866x916 to stay "
            "sharp on a 2x screen."
        ),
    )
    figure_alt = models.CharField(
        max_length=200,
        default="A Media Nest studio set lit for an interview shoot",
        help_text="Described for screen readers and shown if the image fails to load.",
    )
    focal_x = models.PositiveSmallIntegerField(
        default=50,
        help_text="Horizontal focus, 0-100. Move it when the crop cuts the subject.",
    )
    focal_y = models.PositiveSmallIntegerField(
        default=50,
        help_text="Vertical focus, 0-100.",
    )

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "about content"
        verbose_name_plural = "about content"

    def __str__(self):
        return "About content"

    def clean(self):
        if self.focal_x > 100 or self.focal_y > 100:
            raise ValidationError("Focal values are percentages and cannot exceed 100.")
        if self.heading.count("*") not in (0, 2):
            raise ValidationError(
                {"heading": "Use asterisks in a pair, around the one word to accent."}
            )


class Service(models.Model):
    """
    Both service lists, from one table.

    The page shows three services as large cards with a body, an image and
    tags, then six more as names only in a three-column strip. They are the
    same kind of thing at two levels of detail, so `is_featured` decides which
    list a row lands in rather than there being two models.

    **The count is free here**, unlike the About pillars. The cards are a flex
    column and the rail is an ordered list, so nothing tiles and nothing
    breaks when a fourth service is added. The one constraint is on the
    non-featured strip -- see `SERVICE_STRIP_COLUMNS` below.

    Numbers are not stored. The page writes 01-03 for the cards and 04-09 for
    the strip, and the current frontend hardcodes that second range as
    `0{i + 4}` -- which renders "010" on a seventh item and assumes there are
    exactly three featured services. Deriving both from position fixes that.
    """

    title = models.CharField(
        max_length=120,
        help_text='The full name on the card, e.g. "Photography & Brand Visual Presence".',
    )
    short_label = models.CharField(
        max_length=60,
        blank=True,
        help_text='The short name in the left-hand rail, e.g. "Photography". Falls back to the title.',
    )
    body = models.TextField(
        blank=True,
        help_text="Shown under the name in the rail. Featured services only.",
    )
    tags = models.CharField(
        max_length=200,
        blank=True,
        help_text='Comma separated, e.g. "Editorial, Product, Sports, Profiling". Featured services only.',
    )

    image = models.ImageField(
        upload_to="services/",
        blank=True,
        help_text=(
            "The card image. The frame is 457x610 and crops to fill, so upload "
            "at least 914x1220 to stay sharp on a 2x screen."
        ),
    )
    focal_x = models.PositiveSmallIntegerField(default=50, help_text="Horizontal focus, 0-100.")
    focal_y = models.PositiveSmallIntegerField(default=50, help_text="Vertical focus, 0-100.")

    is_featured = models.BooleanField(
        default=False,
        help_text="On: a full card with image, body and tags. Off: name only, in the strip below.",
    )
    is_published = models.BooleanField(default=True, db_index=True)
    order = models.PositiveIntegerField(default=0, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.title

    @property
    def tag_list(self):
        return [t.strip() for t in self.tags.split(",") if t.strip()]

    @property
    def rail_label(self):
        return self.short_label or self.title

    def clean(self):
        if self.focal_x > 100 or self.focal_y > 100:
            raise ValidationError("Focal values are percentages and cannot exceed 100.")
        if self.is_featured and not self.body:
            raise ValidationError(
                {"body": "A featured service is shown as a card, so it needs a description."}
            )


# The non-featured strip is `grid-template-columns: repeat(3, 1fr)`, so a
# count that is not a multiple of three leaves an orphan alone on the last
# row. This is surfaced as a warning in the admin rather than blocking a save:
# refusing to let someone record a discipline the firm genuinely offers, over
# a layout nicety, is the wrong trade.
SERVICE_STRIP_COLUMNS = 3


class Discipline(models.Model):
    """
    A tile in the portfolio grid.

    **The count is free, but only the first eight published tiles are shown.**
    The grid is 12 columns and the eight tiles tessellate it exactly across
    four rows -- 6+6, then 6+3+3, then 5+3+4, then the two tall ones carrying
    into row four. A ninth tile would start a fifth row with eight empty
    columns beside it, so the frontend takes the top eight by order and the
    rest sit in the database unused until someone reorders them up.

    That is why **there is no span field here**. A span belongs to a grid
    position, not to a discipline: slot one is always 6x2 whoever occupies it.
    The frontend holds the eight spans and applies them by position.

    An earlier draft of the plan had span computed in `save()` from the cover's
    dimensions. Measuring the rendered grid showed that is wrong -- slot one is
    a 1.41 box holding a 1.00 image, slot two a 2.82 box holding a 2.00 image.
    Spans do not follow the artwork; they follow the grid.

    A tile holds **either** films **or** stills, never both -- which is how the
    old site worked and how the lightbox reads today.
    """

    # Pixels each slot needs to stay sharp on a 2x screen, in grid order.
    # Measured from the rendered tiles at a 1440 viewport.
    SLOT_SIZES = [
        (1326, 942),  # 1  6x2
        (1326, 470),  # 2  6x1
        (662, 470),   # 3  3x1
        (662, 470),   # 4  3x1
        (1104, 942),  # 5  5x2
        (662, 942),   # 6  3x2
        (882, 470),   # 7  4x1
        (882, 470),   # 8  4x1
    ]
    VISIBLE_TILES = len(SLOT_SIZES)

    name = models.CharField(max_length=80, help_text='The tile label, e.g. "Photography".')
    meta_label = models.CharField(
        max_length=40,
        blank=True,
        help_text='The small word above the name, e.g. "Stills", "Motion", "Broadcast".',
    )
    cover = models.ImageField(
        upload_to="disciplines/",
        blank=True,
        help_text="The tile image. How large it needs to be depends on which slot it lands in.",
    )
    focal_x = models.PositiveSmallIntegerField(default=50, help_text="Horizontal focus, 0-100.")
    focal_y = models.PositiveSmallIntegerField(default=50, help_text="Vertical focus, 0-100.")

    is_published = models.BooleanField(default=True, db_index=True)
    order = models.PositiveIntegerField(default=0, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "id"]
        # Named for where it is on the page, not for what the code calls it.
        # "Disciplines" told an editor nothing about which section it edits;
        # the nav reads Projects while these tiles are on screen and the
        # section's own eyebrow reads Selected work.
        verbose_name = "projects_selected_work"
        verbose_name_plural = "projects_selected_work"

    def __str__(self):
        return self.name

    @property
    def slot(self):
        """Which grid position this occupies, or None if it falls past the eighth."""
        ids = list(
            Discipline.objects.filter(is_published=True).values_list("id", flat=True)[
                : self.VISIBLE_TILES
            ]
        )
        return ids.index(self.id) + 1 if self.id in ids else None

    @property
    def required_size(self):
        s = self.slot
        return self.SLOT_SIZES[s - 1] if s else None

    def clean(self):
        if self.focal_x > 100 or self.focal_y > 100:
            raise ValidationError("Focal values are percentages and cannot exceed 100.")


class DisciplineVideo(models.Model):
    """A film behind a tile. Only the id is stored -- YouTube does the hosting."""

    discipline = models.ForeignKey(Discipline, on_delete=models.CASCADE, related_name="videos")
    youtube_id = models.CharField(
        max_length=20,
        validators=[
            RegexValidator(
                r"^[A-Za-z0-9_-]{11}$",
                "A YouTube id is exactly 11 characters. Paste the id, not the whole URL.",
            )
        ],
        help_text='The 11-character id from the URL: youtube.com/watch?v=<this>',
    )
    title = models.CharField(max_length=120)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "film"
        verbose_name_plural = "films"

    def __str__(self):
        return f"{self.title} ({self.youtube_id})"


class DisciplineImage(models.Model):
    """A still behind a tile, for the disciplines that have no film."""

    discipline = models.ForeignKey(Discipline, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="disciplines/gallery/")
    alt = models.CharField(
        max_length=200,
        help_text="Required — it is read out to screen readers and shown if the image fails.",
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "still"
        verbose_name_plural = "stills"

    def __str__(self):
        return f"{self.discipline.name} — {self.alt[:40]}"


class AboutPillar(models.Model):
    """
    The three cards beside the About figure.

    **The count is fixed at three and the admin disables add and delete.**
    The bento is a 12-column grid and the figure takes 4 columns across 2
    rows, so the pillars have to tile what is left:

        row 1   [figure 4] [pillar 4] [pillar 4]   = 12
        row 2   [figure  ] [pillar 8 wide      ]   = 12

    Three is not a preference, it is what fills the grid. Counts that tile
    without leaving holes are 3, 4, 7, 8, 10 and 11; five, six or nine would
    leave empty cells. Rather than hand an admin that arithmetic, the count is
    fixed and only the text is editable.

    The 01/02/03 labels are not stored. They are the row's position, and a
    stored number goes stale the moment the order changes.
    """

    title = models.CharField(max_length=80)
    body = models.TextField()
    is_wide = models.BooleanField(
        default=False,
        help_text="Spans 8 columns instead of 4. Exactly one pillar should have this.",
    )
    order = models.PositiveIntegerField(default=0, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "about pillar"
        verbose_name_plural = "about pillars"

    def __str__(self):
        return self.title


# Where the left margin's list starts being clipped by the pinned stage.
# Measured by cloning rows into the real rail at five viewports: 13 fit at
# 1024x640, the shortest screen the section still pins on, and more than that
# everywhere taller. Twelve leaves one row of margin.
#
# Nothing else caps the count -- the panels stack rather than tile, and the
# section's height grows with them so the pacing holds. It does grow a lot:
# each reason adds 35vh, so eight of them make the section 380vh of scroll.
# That is an editorial call, not a break, so it is not warned about.
MAX_COMFORTABLE_REASONS = 12

_NUMBER_WORDS = {
    1: "One", 2: "Two", 3: "Three", 4: "Four", 5: "Five", 6: "Six",
    7: "Seven", 8: "Eight", 9: "Nine", 10: "Ten", 11: "Eleven", 12: "Twelve",
}


def number_word(n):
    """
    Spell a small number, so the heading can say "Four reasons" rather than
    "4 reasons". Falls back to the digits past twelve, which is well beyond
    anything this section would hold.
    """
    return _NUMBER_WORDS.get(n, str(n))


class WhyChooseContent(Singleton):
    """
    The framing line above the reasons.

    The heading carries a `{count}` placeholder rather than a written-out
    number. It reads "Four reasons brands stay." today, and the word "Four"
    is not stored anywhere -- the frontend spells the reason count. A stored
    "Four" beside an editable list is the same trap the figures were: add a
    fifth reason and the heading goes on claiming four.

    `*asterisks*` mark the accented span, exactly as AboutContent does.
    """

    heading = models.CharField(
        max_length=120,
        default="{count} reasons brands *stay*.",
        help_text=(
            "Use {count} where the number of reasons should go — it is written "
            "out as a word (Four, Five) and updates itself when reasons are "
            "added or removed. Put *asterisks* around the one accented word."
        ),
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "projects_why_choose_us_heading"
        verbose_name_plural = "projects_why_choose_us_heading"

    def __str__(self):
        return self.heading

    def clean(self):
        super().clean()
        if self.heading.count("*") not in (0, 2):
            raise ValidationError(
                {"heading": "Accent marks come in pairs: *one word* between two asterisks."}
            )
        if "{count}" not in self.heading:
            raise ValidationError(
                {
                    "heading": (
                        "Leave {count} in the heading. Without it the number of "
                        "reasons is written by hand and goes stale the moment one "
                        "is added."
                    )
                }
            )


class Reason(models.Model):
    """
    One reason in the Why Choose Us section.

    **The count is free.** Unlike the About pillars, the reasons do not tile a
    grid -- all of them stack in one box and only the one on show is opaque --
    so a fifth does not leave a hole. Two things follow the count instead of
    constraining it: the heading writes the number out itself, and the
    section's scroll height is computed from it so the panels keep turning
    over at the pace they do now rather than sharing a fixed travel.

    The 01/02/03 labels are not stored. They are the row's position, and a
    stored number goes stale the moment the order changes.

    Neither is a figure. Each reason used to carry one -- 5+ years, nine
    disciplines -- and every one of them was a number About states too, under
    the same label, so the two sections could contradict each other on one
    screen. A number that belongs in a sentence is now written in the
    sentence, and edited as a sentence.
    """

    # Measured on the rendered panel, at the widths where the section pins.
    # The label has to hold one line, and the copy has to fit the box the foot
    # rule sits under, or the composition moves as the reader scrolls.
    LABEL_LIMIT = 25
    BODY_LIMIT = 170

    label = models.CharField(
        max_length=LABEL_LIMIT,
        help_text=(
            f"Set at display size, and it has to stay on one line — "
            f"{LABEL_LIMIT} characters is what fits."
        ),
    )
    body = models.TextField(
        max_length=BODY_LIMIT,
        # A TextField's max_length only sizes the admin's textarea -- unlike a
        # CharField it is enforced neither by validation nor by the database,
        # so on its own it is a suggestion. The validator is what actually
        # keeps a 400-character paragraph out of a box measured for 170.
        validators=[MaxLengthValidator(BODY_LIMIT)],
        help_text=(
            f"Up to {BODY_LIMIT} characters. Past that the copy pushes the "
            f"rule below it and the section shifts as you scroll."
        ),
    )

    is_published = models.BooleanField(default=True, db_index=True)
    order = models.PositiveIntegerField(default=0, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "projects_why_choose_us"
        verbose_name_plural = "projects_why_choose_us"

    def __str__(self):
        return self.label


class TeamContent(Singleton):
    """
    The framing line above the founders.

    Same `{count}` placeholder as the Why Choose heading, for the same reason:
    the line reads "Two photographers running a practice." and the word "Two"
    is spelled from the number of published people rather than stored. A third
    partner would otherwise leave the heading insisting there are two.
    """

    heading = models.CharField(
        max_length=140,
        default="{count} photographers running a *practice*.",
        help_text=(
            "Use {count} where the number of people should go — it is written "
            "out as a word (Two, Three) and updates itself. Put *asterisks* "
            "around the one accented word."
        ),
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "team_the_partners_heading"
        verbose_name_plural = "team_the_partners_heading"

    def __str__(self):
        return self.heading

    def clean(self):
        super().clean()
        if self.heading.count("*") not in (0, 2):
            raise ValidationError(
                {"heading": "Accent marks come in pairs: *one word* between two asterisks."}
            )
        if "{count}" not in self.heading:
            raise ValidationError(
                {
                    "heading": (
                        "Leave {count} in the heading. Without it the number of "
                        "people is written by hand and goes stale the moment one "
                        "is added."
                    )
                }
            )


class Person(models.Model):
    """
    One of the partners.

    **The count is free.** The list is a flex column, not a grid, and the
    left/right flip is decided by row position, so a third person simply adds
    a row mirrored the other way. The heading follows the count; nothing else
    has to.

    The name is two fields because the page sets the surname in italic beside
    the given name -- it is a composition, not a string. One field would mean
    teaching an editor a splitting rule to get the same result.

    The 01/02 in the margin is not stored; it is the row's position.
    """

    # The figure is 460x613 at a 1440 viewport and crops to fill, so this is
    # what it takes to stay sharp on a 2x screen. Worth stating plainly: the
    # two photos seeded here are 375x560, which the frame already upscales.
    PHOTO_SIZE = (920, 1226)

    first_name = models.CharField(max_length=40, help_text="Set in roman, e.g. “Aditi”.")
    last_name = models.CharField(
        max_length=40,
        help_text="Set in the orange italic beneath the given name, e.g. “Singh”.",
    )
    role = models.CharField(max_length=60, help_text='e.g. "Managing Partner".')

    photo = models.ImageField(
        upload_to="team/",
        blank=True,
        help_text=(
            f"Portrait, cropped to 3:4. Upload at least "
            f"{PHOTO_SIZE[0]}x{PHOTO_SIZE[1]} so it stays sharp on a phone or a "
            f"retina screen."
        ),
    )
    focal_x = models.PositiveSmallIntegerField(default=50, help_text="Horizontal focus, 0-100.")
    focal_y = models.PositiveSmallIntegerField(default=50, help_text="Vertical focus, 0-100.")

    is_published = models.BooleanField(default=True, db_index=True)
    order = models.PositiveIntegerField(default=0, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "team_the_partners"
        verbose_name_plural = "team_the_partners"

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def clean(self):
        if self.focal_x > 100 or self.focal_y > 100:
            raise ValidationError("Focal values are percentages and cannot exceed 100.")


class PersonLine(models.Model):
    """One of the dashed lines under a partner's role."""

    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name="lines")
    text = models.CharField(max_length=60, help_text='e.g. "Still Life & Sports Photographer".')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "line"
        verbose_name_plural = "lines"

    def __str__(self):
        return self.text


# The platforms the site links to, for a partner's own account and for the
# firm's. One list: the icon each maps to lives in the frontend beside the
# font that draws it, and two lists here would let the two drift.
SOCIAL_PLATFORMS = [
    ("instagram", "Instagram"),
    ("youtube", "YouTube"),
    ("linkedin", "LinkedIn"),
    ("facebook", "Facebook"),
    ("whatsapp", "WhatsApp"),
]


class PersonSocial(models.Model):
    """
    A partner's own account on one platform.

    The platform is a choice, not a free field. The page renders the icon from
    a CSS class -- `fab fa-instagram` -- and a class typed by hand is both a
    broken icon waiting to happen and a raw class going straight onto the page.
    Choosing the platform also spells the screen-reader label ("Instagram of
    Aditi Singh"), which was written out by hand for every link before.

    The five here are the platforms the site already links to. The icon class
    itself stays in the frontend, next to the icon font that defines it.
    """

    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name="social")
    platform = models.CharField(max_length=20, choices=SOCIAL_PLATFORMS)
    url = models.URLField(max_length=300, help_text="The full link to the profile.")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "social link"
        verbose_name_plural = "social links"

    def __str__(self):
        return f"{self.get_platform_display()} — {self.person}"


class Testimonial(models.Model):
    """
    One quote in the carousel.

    **The count is free.** It is a carousel, not a grid: one testimonial simply
    disables the auto-advance (the component already guards on `count < 2`),
    and the dots below are drawn from the list.

    The quote has a hard limit because the stage does. The carousel used to
    size itself to whatever was in it -- a floor of 300px that grew -- so the
    two quotes measured 311px and 380px and the section grew 68px every nine
    seconds as it advanced itself, carrying the whole page below it. The stage
    is now fixed to hold LIMIT characters at every width; a quote past that
    would start the shifting again, which is why this is validated rather than
    suggested.
    """

    # Measured on the rendered stage at seven widths. 260 characters fits with
    # room to spare everywhere; the tightest case is a 390px phone, where it
    # needs 342px of a 370px box.
    LIMIT = 260

    # 62x62 on the page, so twice that on a retina screen.
    PHOTO_SIZE = (124, 124)

    quote = models.TextField(
        max_length=LIMIT,
        # TextField's max_length only sizes the admin's textarea; unlike a
        # CharField it is enforced neither by validation nor by the database.
        validators=[MaxLengthValidator(LIMIT)],
        help_text=(
            f"Up to {LIMIT} characters. The carousel's box is sized for exactly "
            f"this, so that paging between quotes moves nothing on the page."
        ),
    )
    name = models.CharField(max_length=80)
    role = models.CharField(
        max_length=120,
        help_text='Their title and organisation, e.g. "President, Pan American Billiards & Snooker Association".',
    )
    photo = models.ImageField(
        upload_to="testimonials/",
        blank=True,
        help_text=(
            f"Shown as a {PHOTO_SIZE[0] // 2}px circle, so upload at least "
            f"{PHOTO_SIZE[0]}x{PHOTO_SIZE[1]}. A square crops best."
        ),
    )

    is_published = models.BooleanField(default=True, db_index=True)
    order = models.PositiveIntegerField(default=0, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "team_in_their_words"
        verbose_name_plural = "team_in_their_words"

    def __str__(self):
        return f"{self.name} — {self.quote[:40]}"


class ClientsContent(Singleton):
    """
    The copy above the client cards.

    No `{count}` here, unlike the Why Choose and Team headings: this section
    prints its number in a separate counter beside the grid, which is already
    derived from the list.
    """

    heading = models.CharField(
        max_length=160,
        default="Federations, institutions and *enterprises*.",
        help_text="Wrap one word or phrase in *asterisks* to set it in the orange italic.",
    )
    note = models.TextField(
        default=(
            "The organisations we produce for, across sport, energy and public "
            "enterprise. Together we create stories that move people and build "
            "lasting impact."
        ),
        help_text="The paragraph to the right of the heading.",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "clients_trusted_by_heading"
        verbose_name_plural = "clients_trusted_by_heading"

    def __str__(self):
        return self.heading

    def clean(self):
        super().clean()
        if self.heading.count("*") not in (0, 2):
            raise ValidationError(
                {"heading": "Accent marks come in pairs: *one word* between two asterisks."}
            )


class Client(models.Model):
    """
    One organisation in the grid.

    **The count is free**, with a caveat worth knowing rather than enforcing.
    The grid is four columns wide, three between 821 and 1180px, and two below
    that, so the number that fills every row at every width is a multiple of
    twelve. Eight -- what the site ships with -- fills the four- and two-column
    layouts and leaves one cell short in the three-column one.

    That is not the hole an unfilled About pillar leaves. These are separate
    cards rather than a tessellation, so a short last row reads as a list that
    ended, not as a layout that broke. The admin says which counts fill it and
    leaves the choice alone.

    The 01/02 under each card is the row's position, not a stored field.
    """

    # Columns at each breakpoint, widest first. Their lowest common multiple is
    # what fills every row at every width.
    GRID_COLUMNS = (4, 3, 2)

    # The mark sits in a 74px box and is contained, not cropped, at up to
    # 76x68 -- so twice that to stay sharp on a retina screen. Contained, so
    # no focal point: a logo is never cut.
    LOGO_SIZE = (152, 136)

    name = models.CharField(max_length=60, help_text='As printed on the card, e.g. "Indian Oil".')
    sector = models.CharField(
        max_length=60,
        help_text=(
            'What the organisation is, not a claim about the work — '
            '"International Federation", "Energy".'
        ),
    )
    logo = models.ImageField(
        upload_to="clients/",
        blank=True,
        help_text=(
            f"Shown at up to 76x68 and never cropped, so upload at least "
            f"{LOGO_SIZE[0]}x{LOGO_SIZE[1]}. Transparent or white background."
        ),
    )
    url = models.URLField(
        max_length=300,
        blank=True,
        # URLField allows ftp and ftps by default. This one becomes an
        # external link that opens in a new tab, so only the web schemes.
        validators=[URLValidator(schemes=["http", "https"])],
        help_text=(
            "Optional. With a link the card opens it in a new tab and shows the "
            "arrow badge; without one it is still shown, just not clickable."
        ),
    )

    is_published = models.BooleanField(default=True, db_index=True)
    order = models.PositiveIntegerField(default=0, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "clients_trusted_by"
        verbose_name_plural = "clients_trusted_by"

    def __str__(self):
        return self.name


class ContactContent(Singleton):
    """
    The invitation above the enquiry form.

    The lede carries a `{hours}` placeholder for the same reason the other
    headings carry `{count}`: it says "every day, 24 x 7", which is a figure
    About and the footer also print. Written out here it would be a fourth
    copy to keep in step.

    The form itself is not editable. Its labels, validation messages and
    status line are interface copy rather than content -- they are wired to
    behaviour, they have to stay in step with what the fields actually check,
    and nothing is gained by letting them drift.
    """

    heading = models.CharField(
        max_length=160,
        default="Let us make your brand look *inevitable*.",
        help_text="Wrap one word or phrase in *asterisks* to set it in the orange italic.",
    )
    lede = models.TextField(
        default=(
            "Tell us what you are building. We reply within one working day — "
            "every day, {hours}."
        ),
        help_text=(
            "Use {hours} where the working hours should go — it is filled from "
            "Site settings so this cannot disagree with the rest of the page."
        ),
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "contact_start_a_project"
        verbose_name_plural = "contact_start_a_project"

    def __str__(self):
        return self.heading

    def clean(self):
        super().clean()
        if self.heading.count("*") not in (0, 2):
            raise ValidationError(
                {"heading": "Accent marks come in pairs: *one word* between two asterisks."}
            )


class FooterContent(Singleton):
    """
    The footer's own copy.

    The firm's name is not here -- the wordmark, the contact panel and the
    copyright line all take it from Site settings, so it is written once.

    The blurb reads close to the hero's description on purpose; they are two
    separately written sentences that share a phrase, not one fact stated
    twice, so editing this one cannot make the hero wrong.
    """

    blurb = models.TextField(
        default=(
            "Brand Image Management & Consultancy. Creating and curating "
            "impactful visual content that amplifies brand presence and identity."
        ),
        help_text="The paragraph under the logo.",
    )
    legal_note = models.CharField(
        max_length=120,
        default="All rights reserved.",
        help_text=(
            "Follows the year and the firm's name on the bottom line. The "
            "“© 2026 Media Nest.” part is built from the clock and Site "
            "settings, so it cannot go stale."
        ),
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "footer"
        verbose_name_plural = "footer"

    def __str__(self):
        return "Footer"


class SocialLink(models.Model):
    """
    One of the firm's own accounts.

    Two places show these -- the footer and the header's mobile menu -- so
    they sit beside the firm's other facts rather than under either section.
    The menu used to carry its own list of four, which meant changing an
    account updated the footer and left the menu pointing at the old one.

    WhatsApp is the exception to the URL: its link is built from the phone
    number in Site settings rather than stored, so a changed number cannot
    leave a chat link behind. Leave the URL blank for it.
    """

    platform = models.CharField(max_length=20, choices=SOCIAL_PLATFORMS, unique=True)
    url = models.URLField(
        max_length=300,
        blank=True,
        validators=[URLValidator(schemes=["http", "https"])],
        help_text="Leave blank for WhatsApp — that link is built from the phone number.",
    )
    is_published = models.BooleanField(default=True, db_index=True)
    order = models.PositiveIntegerField(default=0, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "social link"
        verbose_name_plural = "social links"

    def __str__(self):
        return self.get_platform_display()

    def clean(self):
        if self.platform != "whatsapp" and not self.url:
            raise ValidationError({"url": "A link is required for every platform but WhatsApp."})
