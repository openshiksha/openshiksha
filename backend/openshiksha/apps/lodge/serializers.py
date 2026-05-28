from rest_framework import serializers

from .models import Video


class VideoSerializer(serializers.ModelSerializer):
    chapter_name = serializers.CharField(source="chapter.name", read_only=True)

    class Meta:
        model = Video
        fields = [
            "id",
            "chapter",
            "chapter_name",
            "title",
            "embed_url",
            "description",
            "order",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["id", "chapter_name", "created_at"]
