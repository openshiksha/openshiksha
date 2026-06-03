from rest_framework import serializers

from openshiksha.apps.core.models import SubjectRoom, UserRole

from .models import Announcement


class AnnouncementSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()
    subject_room_display = serializers.CharField(source="subject_room.__str__", read_only=True)

    class Meta:
        model = Announcement
        fields = [
            "id",
            "subject_room",
            "subject_room_display",
            "author",
            "author_name",
            "message",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["id", "author", "author_name", "subject_room_display", "created_at"]

    def get_author_name(self, obj) -> str:
        if not obj.author:
            return ""
        return obj.author.get_full_name() or obj.author.username

    def validate_subject_room(self, value: SubjectRoom) -> SubjectRoom:
        user = self.context["request"].user
        if user.role != UserRole.TEACHER or value.teacher_id != user.id:
            raise serializers.ValidationError("You can only post announcements to subject rooms you teach.")
        return value
