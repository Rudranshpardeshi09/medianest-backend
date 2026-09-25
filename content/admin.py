"""
Admin for the content app.

Plain ModelAdmin throughout. Django Admin already does everything this site
needs -- list, form, image upload, ordering, search -- so there is no custom
CMS interface to build.

Two habits run through it:
  * A singleton cannot be added or deleted, and its changelist jumps straight
    to the one row, so nobody has to click through a list of one.
  * Where a count is load-bearing, the admin refuses add and delete rather
    than relying on a note nobody reads.
"""

import math
import re

from django.contrib import admin, messages
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from .models import (
    MAX_COMFORTABLE_REASONS,
    SERVICE_STRIP_COLUMNS,
    AboutContent,
    AboutPillar,
    Client,
    ClientsContent,
    ContactContent,
    ClientsContent,
    Discipline,
    DisciplineImage,
    DisciplineVideo,
    FooterContent,
    Person,
    PersonLine,
    PublishState,
    PersonSocial,
    Reason,
    Service,
    SiteSettings,
    SocialLink,
    TeamContent,
    Testimonial,
    WhyChooseContent,
    number_word,
)


def _rendered_heading(heading, count, noun):
    """
    A heading as the page will print it: {count} filled in and the accented
    span set in the orange italic.

    Both `{count}` headings show this. Without it the admin edits a string
    with a placeholder in it and has to picture the result, which is exactly
    the kind of guessing the placeholder was meant to remove.
    """
    text = heading.replace("{count}", number_word(count))
    head, accent, tail = text, "", ""
    if text.count("*") == 2:
        head, accent, tail = re.split(r"\*(.+?)\*", text, maxsplit=1)
    return format_html(
        '<p style="font-size:17px;margin:0">{}<em style="color:#e95523">{}</em>{}</p>'
        '<p style="margin:6px 0 0;color:#666">With {} published {}.</p>',
        head, accent, tail, count, noun,
    )


class SingletonAdmin(admin.ModelAdmin):
    """One row, reached directly, never added or deleted."""

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        obj = self.model.load()
        return redirect(
            reverse(
                f"admin:{self.model._meta.app_label}_{self.model._meta.model_name}_change",
                args=[obj.pk],
            )
        )


@admin.register(SiteSettings)
class SiteSettingsAdmin(SingletonAdmin):
    fieldsets = (
        ("Brand", {"fields": ("tagline",)}),
        (
            "How to reach us",
            {
                "fields": ("firm_name", "email", ("phone_display", "phone_e164"), "whatsapp_message", "admin_url"),
                "description": (
                    "Printed by the contact panel, the footer and the mobile "
                    "menu. The number is stored twice on purpose: once as it "
                    "should read, once as it must be dialled — the tap-to-call "
                    "and WhatsApp links are built from the second."
                ),
            },
        ),
        (
            "The firm's figures",
            {
                "fields": (
                    "years_of_practice",
                    ("discipline_count", "discipline_count_word"),
                    ("hours_compact", "hours_spaced"),
                    "coverage",
                ),
                "description": (
                    "These appear in several sections at once. Some are written "
                    "two ways on the page on purpose — the hero says “Nine "
                    "disciplines” where the stats row says “9” — so both "
                    "spellings are kept. Change them together."
                ),
            },
        ),
    )
    readonly_fields = ("updated_at",)


@admin.register(AboutContent)
class AboutContentAdmin(SingletonAdmin):
    fieldsets = (
        ("Copy", {"fields": ("heading", "description")}),
        (
            "Figure",
            {
                "fields": ("figure", "preview", "figure_alt", ("focal_x", "focal_y")),
                "description": (
                    "The frame is 433×458 and crops to fill, so part of a wider "
                    "or taller photo will be cut. Move the focal point if the "
                    "crop lands badly."
                ),
            },
        ),
    )
    readonly_fields = ("preview", "updated_at")

    @admin.display(description="Cropped preview")
    def preview(self, obj):
        """
        Shows the image at the frame's real proportions with the same crop the
        site applies. Without this an admin uploads a photo, sees a thumbnail
        that looks fine, and never learns that the page cuts the subject's head
        off.
        """
        if not obj or not obj.figure:
            return "Upload an image to see how it will be cropped."
        return format_html(
            '<div style="width:217px;height:229px;overflow:hidden;border:1px solid #ccc">'
            '<img src="{}" style="width:100%;height:100%;object-fit:cover;'
            'object-position:{}% {}%"></div>'
            '<p style="margin:6px 0 0;color:#666">Shown at half the real size (433×458).</p>',
            obj.figure.url,
            obj.focal_x,
            obj.focal_y,
        )


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("position", "title", "is_featured", "is_published", "order")
    list_editable = ("order", "is_published")
    list_filter = ("is_featured", "is_published")
    search_fields = ("title", "short_label", "body", "tags")
    ordering = ("order", "id")

    fieldsets = (
        ("Listing", {"fields": ("title", "short_label", "is_featured", ("order", "is_published"))}),
        (
            "Card detail",
            {
                "fields": ("body", "tags"),
                "description": "Only shown for featured services. The strip below the cards is names only.",
            },
        ),
        (
            "Card image",
            {
                "fields": ("image", "preview", ("focal_x", "focal_y")),
                "description": (
                    "The frame is 457×610 and crops to fill. Move the focal "
                    "point if the crop lands badly."
                ),
            },
        ),
    )
    readonly_fields = ("preview",)

    @admin.display(description="#")
    def position(self, obj):
        """
        The number the page prints. Featured run 01.., the strip continues
        from where they stop. Derived, never stored -- the frontend's own
        `0{i + 4}` hardcodes both the prefix and the assumption that exactly
        three services are featured.
        """
        group = Service.objects.filter(is_featured=obj.is_featured, is_published=True)
        ids = list(group.values_list("id", flat=True))
        if obj.id not in ids:
            return "--"
        n = ids.index(obj.id) + 1
        if not obj.is_featured:
            n += Service.objects.filter(is_featured=True, is_published=True).count()
        return f"{n:02d}"

    @admin.display(description="Cropped preview")
    def preview(self, obj):
        if not obj or not obj.image:
            return "Upload an image to see how it will be cropped."
        warn = ""
        if obj.image.width < 914 or obj.image.height < 1220:
            warn = format_html(
                '<p style="margin:6px 0 0;color:#c93">This image is {}×{}. The frame '
                'needs 914×1220 to stay sharp on a 2x screen, so it will look soft.</p>',
                obj.image.width,
                obj.image.height,
            )
        return format_html(
            '<div style="width:228px;height:305px;overflow:hidden;border:1px solid #ccc">'
            '<img src="{}" style="width:100%;height:100%;object-fit:cover;'
            'object-position:{}% {}%"></div>'
            '<p style="margin:6px 0 0;color:#666">Half the real size (457×610).</p>{}',
            obj.image.url,
            obj.focal_x,
            obj.focal_y,
            warn,
        )

    def changelist_view(self, request, extra_context=None):
        """
        Warn when the non-featured strip will not fill its rows. Not a block:
        see the note beside SERVICE_STRIP_COLUMNS.
        """
        strip = Service.objects.filter(is_featured=False, is_published=True).count()
        if strip and strip % SERVICE_STRIP_COLUMNS:
            self.message_user(
                request,
                f"The strip below the cards has {strip} entries and lays out in "
                f"{SERVICE_STRIP_COLUMNS} columns, so the last row will be part "
                f"empty. {strip - strip % SERVICE_STRIP_COLUMNS} or "
                f"{strip + SERVICE_STRIP_COLUMNS - strip % SERVICE_STRIP_COLUMNS} "
                f"would fill it.",
                level=messages.WARNING,
            )
        return super().changelist_view(request, extra_context)


class DisciplineVideoInline(admin.TabularInline):
    model = DisciplineVideo
    extra = 0
    fields = ("order", "youtube_id", "title")


class DisciplineImageInline(admin.TabularInline):
    model = DisciplineImage
    extra = 0
    fields = ("order", "image", "alt")


@admin.register(Discipline)
class DisciplineAdmin(admin.ModelAdmin):
    list_display = ("slot_label", "name", "holds", "is_published", "order")
    list_editable = ("order", "is_published")
    ordering = ("order", "id")
    inlines = [DisciplineVideoInline, DisciplineImageInline]

    fieldsets = (
        ("Tile", {"fields": ("name", "meta_label", ("order", "is_published"))}),
        (
            "Cover",
            {
                "fields": ("cover", "preview", ("focal_x", "focal_y")),
                "description": (
                    "Each grid slot is a different size, so how large this needs "
                    "to be depends on where the tile sits. The preview says."
                ),
            },
        ),
    )
    readonly_fields = ("preview",)

    @admin.display(description="Slot")
    def slot_label(self, obj):
        """
        Which of the eight grid positions this holds. Past the eighth a tile is
        stored but not rendered, and saying so is kinder than letting someone
        wonder why their new discipline never appeared.
        """
        s = obj.slot
        if s:
            w, h = Discipline.SLOT_SIZES[s - 1]
            return format_html('{} <span style="color:#888">({}×{})</span>', s, w, h)
        return mark_safe('<span style="color:#c93">not shown</span>')

    @admin.display(description="Holds")
    def holds(self, obj):
        v, i = obj.videos.count(), obj.images.count()
        if v and i:
            return format_html('<span style="color:#c00">{} films + {} stills — pick one</span>', v, i)
        if v:
            return f"{v} film{'s' if v > 1 else ''}"
        if i:
            return f"{i} still{'s' if i > 1 else ''}"
        return mark_safe('<span style="color:#c93">nothing yet</span>')

    @admin.display(description="Cropped preview")
    def preview(self, obj):
        if not obj or not obj.cover:
            return "Upload a cover to see how it will be cropped."
        need = obj.required_size
        if not need:
            note = mark_safe(
                '<p style="margin:6px 0 0;color:#c93">This tile sits past the eighth, '
                'so it is not on the page. Move it up to show it.</p>'
            )
        elif obj.cover.width < need[0] or obj.cover.height < need[1]:
            # State the shortfall rather than a flat "too small". Several of
            # the original covers miss the 2x target by one or two percent,
            # which nobody can see, and a warning that fires identically on
            # those and on an image at half the size is one people learn to
            # ignore.
            short = max(
                round((1 - obj.cover.width / need[0]) * 100),
                round((1 - obj.cover.height / need[1]) * 100),
            )
            note = format_html(
                '<p style="margin:6px 0 0;color:{}">This image is {}×{}. Slot {} wants '
                '{}×{} to be sharp on a 2x screen, so it is {}% short.</p>',
                "#c93" if short > 10 else "#666",
                obj.cover.width, obj.cover.height, obj.slot, need[0], need[1], short,
            )
        else:
            note = format_html('<p style="margin:6px 0 0;color:#484">Large enough for slot {}.</p>', obj.slot)
        return format_html(
            '<div style="width:240px;height:170px;overflow:hidden;border:1px solid #ccc">'
            '<img src="{}" style="width:100%;height:100%;object-fit:cover;'
            'object-position:{}% {}%"></div>{}',
            obj.cover.url, obj.focal_x, obj.focal_y, note,
        )

    def changelist_view(self, request, extra_context=None):
        published = Discipline.objects.filter(is_published=True).count()
        if published < Discipline.VISIBLE_TILES:
            self.message_user(
                request,
                f"The grid has {Discipline.VISIBLE_TILES} slots and {published} "
                f"published tiles, so the last row will have gaps.",
                level=messages.WARNING,
            )
        elif published > Discipline.VISIBLE_TILES:
            self.message_user(
                request,
                f"{published} tiles are published but the grid shows the first "
                f"{Discipline.VISIBLE_TILES}. Reorder to change which ones appear.",
                level=messages.INFO,
            )
        mixed = [d.name for d in Discipline.objects.all() if d.videos.exists() and d.images.exists()]
        if mixed:
            self.message_user(
                request,
                f"A tile shows either films or stills, not both. Fix: {', '.join(mixed)}.",
                level=messages.ERROR,
            )
        return super().changelist_view(request, extra_context)


@admin.register(AboutPillar)
class AboutPillarAdmin(admin.ModelAdmin):
    list_display = ("position", "title", "is_wide", "order")
    list_editable = ("order",)
    ordering = ("order", "id")

    @admin.display(description="#")
    def position(self, obj):
        """The 01/02/03 the page shows. Derived, never stored."""
        ids = list(AboutPillar.objects.values_list("id", flat=True))
        return f"{ids.index(obj.id) + 1:02d}" if obj.id in ids else "--"

    def has_add_permission(self, request):
        """
        Three is what fills the grid — see the model docstring. A fourth
        pillar would sit in a row of its own with eight empty columns beside
        it, so the count is closed rather than left to be discovered.
        """
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(WhyChooseContent)
class WhyChooseContentAdmin(SingletonAdmin):
    fields = ("heading", "rendered")
    readonly_fields = ("rendered", "updated_at")

    @admin.display(description="As the page will read it")
    def rendered(self, obj):
        if not obj:
            return "—"
        return _rendered_heading(
            obj.heading, Reason.objects.filter(is_published=True).count(), "reasons"
        )


@admin.register(Reason)
class ReasonAdmin(admin.ModelAdmin):
    list_display = ("position", "label", "length", "is_published", "order")
    list_editable = ("order", "is_published")
    list_filter = ("is_published",)
    search_fields = ("label", "body")
    ordering = ("order", "id")

    fieldsets = (
        (
            None,
            {
                "fields": ("label", "body", ("order", "is_published")),
                "description": (
                    "Add or remove reasons freely — they stack rather than tile, "
                    "so the layout does not break. The heading writes the count "
                    "out itself and the section grows to keep the pace."
                ),
            },
        ),
    )

    @admin.display(description="#")
    def position(self, obj):
        """The 01/02/03 the page shows. Derived, never stored."""
        ids = list(Reason.objects.filter(is_published=True).values_list("id", flat=True))
        return f"{ids.index(obj.id) + 1:02d}" if obj.id in ids else "--"

    @admin.display(description="Length")
    def length(self, obj):
        """
        How close each field is to the limit. The limits are the panel's real
        measurements, so "near" here means the composition is about to move.
        """
        parts = []
        for name, used, cap in (
            ("label", len(obj.label), Reason.LABEL_LIMIT),
            ("copy", len(obj.body), Reason.BODY_LIMIT),
        ):
            colour = "#c00" if used > cap else "#c93" if used > cap * 0.9 else "#666"
            parts.append(f'<span style="color:{colour}">{name} {used}/{cap}</span>')
        return mark_safe(" · ".join(parts))

    def changelist_view(self, request, extra_context=None):
        n = Reason.objects.filter(is_published=True).count()
        if n < 2:
            self.message_user(
                request,
                f"{n} published reason{'s' if n != 1 else ''}. The section scrubs "
                f"one reason into the next as you scroll, so it needs at least two "
                f"to have anything to do.",
                level=messages.WARNING,
            )
        elif n > MAX_COMFORTABLE_REASONS:
            self.message_user(
                request,
                f"{n} published reasons. The list in the left margin is only as "
                f"tall as the pinned stage, and past {MAX_COMFORTABLE_REASONS} "
                f"rows it is cut off on a short laptop screen. The section also "
                f"grows 35vh per reason — this one is now "
                f"{100 + n * 35}vh of scroll.",
                level=messages.WARNING,
            )
        return super().changelist_view(request, extra_context)


@admin.register(TeamContent)
class TeamContentAdmin(SingletonAdmin):
    fields = ("heading", "rendered")
    readonly_fields = ("rendered", "updated_at")

    @admin.display(description="As the page will read it")
    def rendered(self, obj):
        if not obj:
            return "—"
        n = Person.objects.filter(is_published=True).count()
        return _rendered_heading(obj.heading, n, "people")


class PersonLineInline(admin.TabularInline):
    model = PersonLine
    extra = 0
    fields = ("order", "text")


class PersonSocialInline(admin.TabularInline):
    model = PersonSocial
    extra = 0
    fields = ("order", "platform", "url")


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ("position", "__str__", "role", "holds", "is_published", "order")
    list_editable = ("order", "is_published")
    list_filter = ("is_published",)
    search_fields = ("first_name", "last_name", "role")
    ordering = ("order", "id")
    inlines = [PersonLineInline, PersonSocialInline]

    fieldsets = (
        (
            "Name",
            {
                "fields": (("first_name", "last_name"), "role"),
                "description": "The surname is set in the orange italic beneath the given name.",
            },
        ),
        ("Listing", {"fields": (("order", "is_published"),)}),
        (
            "Portrait",
            {
                "fields": ("photo", "preview", ("focal_x", "focal_y")),
                "description": (
                    "Cropped to 3:4 and filled, so a wider or taller photo loses "
                    "its edges. Move the focal point if the crop cuts the face."
                ),
            },
        ),
    )
    readonly_fields = ("preview",)

    @admin.display(description="#")
    def position(self, obj):
        """The 01/02 in the margin. Derived, never stored."""
        ids = list(Person.objects.filter(is_published=True).values_list("id", flat=True))
        return f"{ids.index(obj.id) + 1:02d}" if obj.id in ids else "--"

    @admin.display(description="Holds")
    def holds(self, obj):
        lines, social = obj.lines.count(), obj.social.count()
        bits = [f"{lines} line{'s' if lines != 1 else ''}"]
        if social:
            bits.append(f"{social} link{'s' if social != 1 else ''}")
        else:
            bits.append('<span style="color:#c93">no links</span>')
        return mark_safe(" · ".join(bits))

    @admin.display(description="Cropped preview")
    def preview(self, obj):
        if not obj or not obj.photo:
            return "Upload a portrait to see how it will be cropped."
        need = Person.PHOTO_SIZE
        if obj.photo.width < need[0] or obj.photo.height < need[1]:
            short = max(
                round((1 - obj.photo.width / need[0]) * 100),
                round((1 - obj.photo.height / need[1]) * 100),
            )
            note = format_html(
                '<p style="margin:6px 0 0;color:{}">This photo is {}×{}. The frame '
                'wants {}×{} to be sharp on a phone or a retina screen, so it is '
                '{}% short and will be stretched.</p>',
                "#c93" if short > 10 else "#666",
                obj.photo.width, obj.photo.height, need[0], need[1], short,
            )
        else:
            note = mark_safe('<p style="margin:6px 0 0;color:#484">Large enough for the frame.</p>')
        return format_html(
            '<div style="width:230px;height:307px;overflow:hidden;border:1px solid #ccc">'
            '<img src="{}" style="width:100%;height:100%;object-fit:cover;'
            'object-position:{}% {}%"></div>'
            '<p style="margin:6px 0 0;color:#666">Half the real size (460×613).</p>{}',
            obj.photo.url, obj.focal_x, obj.focal_y, note,
        )

    def changelist_view(self, request, extra_context=None):
        published = Person.objects.filter(is_published=True)
        if not published.exists():
            self.message_user(
                request,
                "No published people, so the section renders a heading and nothing else.",
                level=messages.WARNING,
            )
        # A published person with no portrait leaves an empty frame on the
        # page. The frame keeps its shape so nothing breaks, but the row is
        # half blank and that is worth saying out loud.
        photoless = [str(p) for p in published if not p.photo]
        if photoless:
            self.message_user(
                request,
                f"No portrait uploaded for {', '.join(photoless)}, so the frame "
                f"beside the name is empty on the page.",
                level=messages.WARNING,
            )
        return super().changelist_view(request, extra_context)


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ("position", "name", "role", "length", "is_published", "order")
    list_editable = ("order", "is_published")
    list_filter = ("is_published",)
    search_fields = ("name", "role", "quote")
    ordering = ("order", "id")

    fieldsets = (
        (
            "Quote",
            {
                "fields": ("quote",),
                "description": (
                    "The carousel's box is sized for the character limit, so "
                    "paging between quotes moves nothing. Going over is refused "
                    "rather than allowed to shift the page."
                ),
            },
        ),
        ("Who said it", {"fields": ("name", "role")}),
        ("Portrait", {"fields": ("photo", "preview")}),
        ("Listing", {"fields": (("order", "is_published"),)}),
    )
    readonly_fields = ("preview",)

    @admin.display(description="#")
    def position(self, obj):
        ids = list(Testimonial.objects.filter(is_published=True).values_list("id", flat=True))
        return f"{ids.index(obj.id) + 1:02d}" if obj.id in ids else "--"

    @admin.display(description="Length")
    def length(self, obj):
        used, cap = len(obj.quote), Testimonial.LIMIT
        colour = "#c00" if used > cap else "#c93" if used > cap * 0.9 else "#666"
        return mark_safe(f'<span style="color:{colour}">{used}/{cap}</span>')

    @admin.display(description="As it will appear")
    def preview(self, obj):
        if not obj or not obj.photo:
            return "Upload a portrait to see it as the page crops it."
        need = Testimonial.PHOTO_SIZE
        if obj.photo.width < need[0] or obj.photo.height < need[1]:
            note = format_html(
                '<p style="margin:6px 0 0;color:#c93">This photo is {}×{}. It is shown '
                'as a {}px circle, so it needs {}×{} to stay sharp on a retina screen.</p>',
                obj.photo.width, obj.photo.height, need[0] // 2, need[0], need[1],
            )
        else:
            note = mark_safe('<p style="margin:6px 0 0;color:#484">Large enough.</p>')
        return format_html(
            '<div style="width:62px;height:62px;border-radius:50%;overflow:hidden;'
            'border:1px solid #ccc"><img src="{}" style="width:100%;height:100%;'
            'object-fit:cover"></div>{}',
            obj.photo.url, note,
        )

    def changelist_view(self, request, extra_context=None):
        n = Testimonial.objects.filter(is_published=True).count()
        if n == 0:
            self.message_user(
                request,
                "No published testimonials, so the whole section is left off the "
                "page. An empty carousel reads as broken rather than as absent.",
                level=messages.WARNING,
            )
        elif n == 1:
            self.message_user(
                request,
                "One published testimonial. The arrows and dots still draw, but "
                "there is nothing to page to and the auto-advance stays off.",
                level=messages.INFO,
            )
        return super().changelist_view(request, extra_context)


@admin.register(ClientsContent)
class ClientsContentAdmin(SingletonAdmin):
    fields = ("heading", "note")
    readonly_fields = ("updated_at",)


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("position", "name", "sector", "mark", "links", "is_published", "order")
    list_editable = ("order", "is_published")
    list_filter = ("is_published",)
    search_fields = ("name", "sector")
    ordering = ("order", "id")

    fieldsets = (
        ("Organisation", {"fields": ("name", "sector")}),
        (
            "Mark",
            {
                "fields": ("logo", "preview"),
                "description": (
                    "Contained in a fixed box rather than cropped, so marks of "
                    "very different proportions still line up across the row."
                ),
            },
        ),
        ("Link", {"fields": ("url",)}),
        ("Listing", {"fields": (("order", "is_published"),)}),
    )
    readonly_fields = ("preview",)

    @admin.display(description="#")
    def position(self, obj):
        ids = list(Client.objects.filter(is_published=True).values_list("id", flat=True))
        return f"{ids.index(obj.id) + 1:02d}" if obj.id in ids else "--"

    @admin.display(description="Mark")
    def mark(self, obj):
        if not obj.logo:
            return mark_safe('<span style="color:#c93">none</span>')
        return format_html(
            '<img src="{}" style="height:26px;width:auto;max-width:60px;object-fit:contain">',
            obj.logo.url,
        )

    @admin.display(description="Link")
    def links(self, obj):
        return mark_safe(
            '<span style="color:#666">opens in a new tab</span>'
            if obj.url
            else '<span style="color:#888">not clickable</span>'
        )

    @admin.display(description="As the card will show it")
    def preview(self, obj):
        if not obj or not obj.logo:
            return "Upload a mark to see it at the size the card uses."
        need = Client.LOGO_SIZE
        if obj.logo.width < need[0] or obj.logo.height < need[1]:
            note = format_html(
                '<p style="margin:6px 0 0;color:#c93">This mark is {}×{}. It needs '
                '{}×{} to stay sharp on a retina screen.</p>',
                obj.logo.width, obj.logo.height, need[0], need[1],
            )
        else:
            note = mark_safe('<p style="margin:6px 0 0;color:#484">Large enough.</p>')
        return format_html(
            '<div style="width:100%;max-width:200px;height:74px;display:grid;'
            'place-items:center;border:1px solid #ccc;background:#fff">'
            '<img src="{}" style="max-width:76px;max-height:68px;width:auto;'
            'height:auto;object-fit:contain"></div>{}',
            obj.logo.url, note,
        )

    def changelist_view(self, request, extra_context=None):
        n = Client.objects.filter(is_published=True).count()
        short = [c for c in Client.GRID_COLUMNS if n % c]
        if n and short:
            fills = Client.GRID_COLUMNS[0]
            for c in Client.GRID_COLUMNS[1:]:
                fills = fills * c // math.gcd(fills, c)
            lower, upper = (n // fills) * fills, ((n // fills) + 1) * fills
            self.message_user(
                request,
                f"{n} published. The grid is "
                f"{', '.join(str(c) for c in Client.GRID_COLUMNS)} columns wide as "
                f"the screen narrows, so the last row is part empty at "
                f"{', '.join(str(c) for c in short)} columns. "
                f"{lower or fills} or {upper} would fill every row at every width.",
                level=messages.INFO,
            )
        return super().changelist_view(request, extra_context)


@admin.register(ContactContent)
class ContactContentAdmin(SingletonAdmin):
    fields = ("heading", "lede", "rendered")
    readonly_fields = ("rendered", "updated_at")

    @admin.display(description="As the page will read it")
    def rendered(self, obj):
        if not obj:
            return "—"
        hours = SiteSettings.load().hours_spaced
        head, accent, tail = obj.heading, "", ""
        if obj.heading.count("*") == 2:
            head, accent, tail = re.split(r"\*(.+?)\*", obj.heading, maxsplit=1)
        return format_html(
            '<p style="font-size:17px;margin:0">{}<em style="color:#e95523">{}</em>{}</p>'
            '<p style="margin:8px 0 0">{}</p>',
            head, accent, tail, obj.lede.replace("{hours}", hours),
        )


@admin.register(FooterContent)
class FooterContentAdmin(SingletonAdmin):
    fields = ("blurb", "legal_note", "bottom_line")
    readonly_fields = ("bottom_line", "updated_at")

    @admin.display(description="The bottom line reads")
    def bottom_line(self, obj):
        if not obj:
            return "—"
        from datetime import date

        return f"© {date.today().year} {SiteSettings.load().firm_name}. {obj.legal_note}"


@admin.register(SocialLink)
class SocialLinkAdmin(admin.ModelAdmin):
    list_display = ("platform", "target", "is_published", "order")
    list_editable = ("order", "is_published")
    ordering = ("order", "id")
    fields = ("platform", "url", ("order", "is_published"))

    @admin.display(description="Goes to")
    def target(self, obj):
        if obj.platform == "whatsapp":
            s = SiteSettings.load()
            return mark_safe(
                f'<span style="color:#666">built from the phone number — '
                f"{s.phone_e164}</span>"
            )
        return obj.url or mark_safe('<span style="color:#c00">missing</span>')


@admin.register(PublishState)
class PublishStateAdmin(SingletonAdmin):
    """
    Read-only. The record is written by the publish button, not by hand --
    editing it would only make the index lie about what is live.
    """

    readonly_fields = ("last_triggered_at", "last_error")
    fields = ("last_triggered_at", "last_error")

    def has_change_permission(self, request, obj=None):
        return False
