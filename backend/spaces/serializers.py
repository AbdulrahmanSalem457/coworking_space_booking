from rest_framework import serializers

from .models import Space


class SpaceSerializer(serializers.ModelSerializer):
    """Used for both the space list and the space detail endpoints."""

    class Meta:
        model = Space
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "capacity",
            "price_per_hour",
            "image",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["id", "slug", "created_at"]
