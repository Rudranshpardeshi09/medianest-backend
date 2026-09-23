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

from django.contrib import admin, messages
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from .models import (
    SERVICE_STRIP_COLUMNS,
    AboutContent,
    AboutPillar,
    Discipline,
    DisciplineImage,
    DisciplineVideo,
    Service,
    SiteSettings,
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
