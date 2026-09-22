from django.db import connection
from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(["GET"])
def health(request):
    """
    Liveness plus a real database round trip, so a host health check fails
    when the database is unreachable rather than reporting green on a
    process that cannot serve anything.
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        database = "ok"
        status = 200
    except Exception:
        database = "unreachable"
        status = 503

    return Response({"status": "ok" if status == 200 else "degraded",
                     "database": database}, status=status)
