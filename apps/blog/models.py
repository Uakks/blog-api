"""Blog models: category, tag, post and comment."""

from django.conf import settings
from django.db.models import (
    CASCADE,
    SET_NULL,
    CharField,
    DateTimeField,
    ForeignKey,
    ManyToManyField,
    Model,
    SlugField,
    TextChoices,
    TextField,
)


class Category(Model):
    """Blog post category."""

    NAME_MAX_LENGTH = 100
    SLUG_MAX_LENGTH = 100

    name = CharField(max_length=NAME_MAX_LENGTH, unique=True)
    slug = SlugField(max_length=SLUG_MAX_LENGTH, unique=True)

    class Meta:
        ordering = ("name",)
        verbose_name_plural = "categories"

    def __str__(self) -> str:
        return self.name


class Tag(Model):
    """Optional tag for posts."""

    NAME_MAX_LENGTH = 50
    SLUG_MAX_LENGTH = 50

    name = CharField(max_length=NAME_MAX_LENGTH, unique=True)
    slug = SlugField(max_length=SLUG_MAX_LENGTH, unique=True)

    class Meta:
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name


class Post(Model):
    """Post belongs to a user, has one optional category and many tags."""

    TITLE_MAX_LENGTH = 200
    SLUG_MAX_LENGTH = 220
    STATUS_MAX_LENGTH = 9

    class Status(TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"

    author = ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=CASCADE, related_name="posts"
    )
    title = CharField(max_length=TITLE_MAX_LENGTH)
    slug = SlugField(max_length=SLUG_MAX_LENGTH, unique=True)
    body = TextField()
    category = ForeignKey(
        Category,
        on_delete=SET_NULL,
        null=True,
        blank=True,
        related_name="posts",
    )
    tags = ManyToManyField(Tag, blank=True, related_name="posts")
    status = CharField(
        max_length=STATUS_MAX_LENGTH,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return self.title


class Comment(Model):
    """Comment written by a user on a post."""

    post = ForeignKey(Post, on_delete=CASCADE, related_name="comments")
    author = ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=CASCADE, related_name="comments"
    )
    body = TextField()
    created_at = DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"Comment {self.pk} on {self.post_id}"
