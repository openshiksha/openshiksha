from rest_framework import serializers

from .models import Enquirer


class EnquirerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enquirer
        fields = ["id", "name", "school", "email", "phone", "message", "created_at"]
        read_only_fields = ["id", "created_at"]
