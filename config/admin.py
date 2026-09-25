"""
The admin site itself.

Only reason it is subclassed: the index page needs to know whether what is
saved has actually been published. The site is static -- content is baked in
when Vercel builds -- so an edit here changes nothing a visitor sees until the
site is rebuilt, and that is the one thing about this setup that surprises
people. The index says it plainly.

Computed in `index()` rather than `each_context()` on purpose: the freshness
check reads the newest row from every content table, and there is no reason to
pay for that on every change form.
"""

from django.contrib.admin import AdminSite
from django.contrib.admin.apps import AdminConfig
from django.utils.timesince import timesince


class MediaNestAdminSite(AdminSite):
    site_header = "Media Nest"
    site_title = "Media Nest"
    index_title = "Site content"

    def index(self, request, extra_context=None):
        # Imported here, not at module level: this runs during app loading and
        # the models are not ready yet.
        from content.models import PublishState
        from content.views import _last_modified

        state = PublishState.load()
        changed = _last_modified()

        context = {
            "publish_state": state,
            "published_ago": (
                f"{timesince(state.last_triggered_at)} ago"
                if state.last_triggered_at
                else "never"
            ),
            # PublishState is deliberately not among the tables `_last_modified`
            # looks at -- if it were, recording a publish would immediately
            # count as a change and the panel would never read as up to date.
            "unpublished": bool(
                changed
                and (state.last_triggered_at is None or changed > state.last_triggered_at)
            ),
        }
        context.update(extra_context or {})
        return super().index(request, context)


class MediaNestAdminConfig(AdminConfig):
    default_site = "config.admin.MediaNestAdminSite"
