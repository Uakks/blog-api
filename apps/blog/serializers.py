"""Serializer representations and validations for blog resources."""

from rest_framework import serializers

from apps.auths.models import User
from apps.blog.models import Category, Comment, Post, Tag


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "name", "slug")


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ("id", "name", "slug")


class PostSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(slug_field="email", read_only=True)
    category = serializers.SlugRelatedField(
        slug_field="slug",
        queryset=Category.objects.all(),
        allow_null=True,
        required=False,
    )
    tags = serializers.SlugRelatedField(
        slug_field="slug", queryset=Tag.objects.all(), many=True, required=False
    )

    class Meta:
        model = Post
        fields = (
            "id", "author", "title", "slug", "body", "category", "tags", "status",
            "created_at", "updated_at",
        )
        read_only_fields = ("id", "author", "created_at", "updated_at")


class CommentSerializer(serializers.ModelSerializer):
    post = serializers.SlugRelatedField(slug_field="slug", queryset=Post.objects.all())
    author = serializers.SlugRelatedField(slug_field="email", read_only=True)

    class Meta:
        model = Comment
        fields = ("id", "post", "author", "body", "created_at")
        read_only_fields = ("id", "author", "created_at")

    def validate_post(self, post: Post) -> Post:
        request = self.context["request"]
        user: User = request.user
        if self.instance and self.instance.post_id != post.pk:
            raise serializers.ValidationError(
                "A comment cannot be moved to another post."
            )
        if post.status != Post.Status.PUBLISHED and not (
            user.is_authenticated and (post.author_id == user.pk or user.is_staff)
        ):
            raise serializers.ValidationError(
                "This post is not available for comments."
            )
        return post
