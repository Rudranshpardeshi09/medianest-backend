"""
Serializers for the public content payload.

Read-only. Nothing here accepts input -- the only write endpoint on the site
is the contact form, which lives in its own app.

Shapes are chosen to match what the components already render, so the
frontend swap is a change of source and not a change of structure. Where the
page derives something from position (the 01/02/03 labels), it is derived
here too rather than stored, so the two can never disagree.
"""

from rest_framework import serializers

from .models import AboutContent, AboutPillar, Service, SiteSettings


class SiteSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteSettings
        fields = [
            "tagline",
            "years_of_practice",
            "discipline_count",
            "discipline_count_word",
            "hours_compact",
            "hours_spaced",
            "coverage",
        ]


class AboutPillarSerializer(serializers.ModelSerializer):
    class Meta:
        model = AboutPillar
        fields = ["title", "body", "is_wide"]


class AboutContentSerializer(serializers.ModelSerializer):
    figure = serializers.SerializerMethodField()
    pillars = serializers.SerializerMethodField()

    class Meta:
        model = AboutContent
        fields = ["heading", "description", "figure", "figure_alt", "focal_x", "focal_y", "pillars"]

    def get_figure(self, obj):
        if not obj.figure:
            return None
        request = self.context.get("request")
        url = obj.figure.url
        return request.build_absolute_uri(url) if request else url

    def get_pillars(self, obj):
        return AboutPillarSerializer(AboutPillar.objects.all(), many=True).data


class ServiceSerializer(serializers.ModelSerializer):
    label = serializers.CharField(source="rail_label", read_only=True)
    tags = serializers.ListField(source="tag_list", read_only=True)
    image = serializers.SerializerMethodField()

    class Meta:
        model = Service
        fields = ["title", "label", "body", "tags", "image", "focal_x", "focal_y", "is_featured"]

    def get_image(self, obj):
        if not obj.image:
            return None
        request = self.context.get("request")
        url = obj.image.url
        return request.build_absolute_uri(url) if request else url
