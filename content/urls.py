from django.urls import path

from .views import content

urlpatterns = [path("content/", content, name="content")]
