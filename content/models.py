"""
Content models.

Built section by section against the live frontend rather than all at once,
so every field here exists because something on the page renders it. See
IMPLEMENTATION PLAN.md section 12a for the decisions behind each one.

Built so far: Site settings, About.
"""

from django.core.exceptions import ValidationError
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
