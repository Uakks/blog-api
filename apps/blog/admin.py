"""Django admin configuration for blog models."""

from django.contrib.admin import ModelAdmin, register

from apps.blog.models import Category, Comment, Post, Tag


@register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@register(Tag)
class TagAdmin(ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@register(Post)
class PostAdmin(ModelAdmin):
    list_display = ("title", "author", "category", "status", "created_at")
    list_filter = ("status", "category")
    search_fields = ("title", "author__email")
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("tags",)
    readonly_fields = ("created_at", "updated_at")


@register(Comment)
class CommentAdmin(ModelAdmin):
    list_display = ("post", "author", "created_at")
    search_fields = ("body", "post__title")
