"""Validate user registration using the custom email-based model."""

from rest_framework import serializers

from django.contrib.auth.password_validation import validate_password

from apps.auths.models import User


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ("id", "email", "first_name", "last_name", "password")
        read_only_fields = ("id",)

    def validate_email(self, value: str) -> str:
        email = value.strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("Email already registered.")
        return email

    def create(self, validated_data: dict[str, object]) -> User:
        return User.objects.create_user(**validated_data)
