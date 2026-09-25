"""
The "publish changes" button.

The site is static: the frontend reads `/api/content/` once while Vercel
builds and bakes the result into the bundle, so a visitor never talks to this
server -- and an edit in the admin is not live until Vercel builds again.

This gives that a button. It calls a Vercel Deploy Hook, which is a URL that
starts a build and needs no credentials beyond itself.

Done server side rather than from the admin's browser because PythonAnywhere
turned out to allow the outbound call (its free tier blocks most, so this was
checked rather than assumed). Server side is better here: the hook URL stays
in the environment instead of being printed into a page, and a failure can be
reported honestly rather than guessed at.
"""

import json
import urllib.error
import urllib.request

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponseNotAllowed
from django.shortcuts import redirect
from django.utils import timezone
from django.views.decorators.http import require_POST

from config.settings.base import env

from .models import PublishState

TIMEOUT = 20


@staff_member_required
@require_POST
def publish(request):
    hook = env("VERCEL_DEPLOY_HOOK", "").strip()
    state = PublishState.load()

    if not hook:
        state.last_error = "No VERCEL_DEPLOY_HOOK is set on the server."
        state.save()
        messages.error(
            request,
            "No deploy hook is configured, so nothing was triggered. Set "
            "VERCEL_DEPLOY_HOOK in the server's .env and reload the web app.",
        )
        return redirect("admin:index")

    req = urllib.request.Request(hook, data=b"", method="POST")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as res:
            body = res.read(400).decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        detail = e.read(300).decode("utf-8", "replace")
        state.last_error = f"Vercel answered {e.code}: {detail}"
        state.save()
        messages.error(request, f"Vercel refused the request ({e.code}). {detail}")
        return redirect("admin:index")
    except Exception as e:  # network, timeout, DNS
        state.last_error = f"{type(e).__name__}: {e}"
        state.save()
        messages.error(request, f"Could not reach Vercel: {e}")
        return redirect("admin:index")

    state.last_triggered_at = timezone.now()
    state.last_error = ""
    state.save()

    # The hook answers with the job it queued; showing the id makes the build
    # findable in Vercel rather than leaving "it worked" to be taken on trust.
    try:
        job = json.loads(body).get("job", {}).get("id", "")
    except (ValueError, AttributeError):
        job = ""
    messages.success(
        request,
        "Vercel is rebuilding the site" + (f" (build {job})." if job else ".")
        + " It usually takes a minute or two; refresh the site after that.",
    )
    return redirect("admin:index")
