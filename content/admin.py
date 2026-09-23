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

from .models import (
    SERVICE_STRIP_COLUMNS,
    AboutContent,
    AboutPillar,
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
