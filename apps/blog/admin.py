"""Django admin configuration for blog models."""

from django.contrib import admin
from django.contrib.admin import register
from django.db import models
from django.db.models import Count, Prefetch

from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse
from urllib.parse import urlencode

from unfold.admin import ModelAdmin, TabularInline
from unfold.contrib.filters.admin import (
    ChoicesDropdownFilter,
    RelatedDropdownFilter,
    MultipleRelatedDropdownFilter,
    AutocompleteSelectFilter,
    RangeDateTimeFilter,
)
from unfold.contrib.forms.widgets import WysiwygWidget
from unfold.decorators import display, action
from unfold.sections import TableSection

from apps.blog.models import Category, Post, Comment, Tag

class CategoryPostsSection(TableSection):
    verbose_name = "Posts in this category"
    related_name = "posts"
    fields = ["title", "status", "created_at"]


@register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ("name", "post_count")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}
    list_sections = [CategoryPostsSection]

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(
            _post_count=Count("posts", distinct=True)
        ).prefetch_related("posts")

    @display(description="Number of posts", ordering="_post_count")
    def post_count(self, obj):
        return obj._post_count


@register(Tag)
class TagAdmin(ModelAdmin):
    list_display = ("name", "post_count")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(
            _post_count=Count("posts", distinct=True)
        )

    @display(description="Number of posts", ordering="_post_count")
    def post_count(self, obj):
        return obj._post_count


class PostCommentsSection(TableSection):
    verbose_name = "Comments"
    related_name = "comments"
    fields = ["author", "body", "created_at"]


class CommentInline(TabularInline):
    model = Comment
    extra = 0
    per_page = 10
    tab = True
    fields = ("author", "body", "created_at")
    readonly_fields = ("created_at",)


@register(Post)
class PostAdmin(ModelAdmin):
    list_display = (
        "post_header",
        "status_label",
        "category",
        "tags_dropdown",
        "comment_count",
        "created_at",
    )
    list_filter = (
        ("status", ChoicesDropdownFilter),
        ("category", RelatedDropdownFilter),
        ("tags", MultipleRelatedDropdownFilter),
        ("author", AutocompleteSelectFilter),
        ("created_at", RangeDateTimeFilter),
    )
    list_filter_submit = True

    search_fields = (
        "title",
        "body",
        "author__email",
    )

    list_per_page = 20
    list_sections = [PostCommentsSection]

    # Editing form
    fieldsets = (
        (
            "Content",
            {
                "classes": ("tab",),
                "fields": ("title", "slug", "body"),
            },
        ),
        (
            "Classification",
            {
                "classes": ("tab",),
                "fields": ("category", "tags", "status"),
            },
        ),
        (
            "Meta",
            {
                "classes": ("tab",),
                "fields": (
                    "author",
                    "created_at",
                    "updated_at",
                ),
            },
        ),
    )

    prepopulated_fields = {"slug": ("title",)}
    autocomplete_fields = ("author", "category", "tags")
    readonly_fields = ("created_at", "updated_at")
    warn_unsaved_form = True

    formfield_overrides = {
        models.TextField: {"widget": WysiwygWidget},
    }

    inlines = [CommentInline]

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("author", "category")
            .prefetch_related(
                "tags",
                Prefetch(
                    "comments",
                    queryset=Comment.objects.select_related("author"),
                ),
            )
            .annotate(
                _comment_count=Count("comments", distinct=True)
            )
        )

    @display(description="Post", header=True)
    def post_header(self, obj):
        return obj.title, obj.author.email

    @display(
        description="Status",
        ordering="status",
        label={
            "published": "success",
            "draft": "warning",
        },
    )
    def status_label(self, obj):
        return obj.status

    @display(description="Tags", dropdown=True)
    def tags_dropdown(self, obj):
        tags = list(obj.tags.all())

        return {
            "title": f"{len(tags)} tags",
            "items": [
                {"title": tag.name}
                for tag in tags
            ],
        }

    @display(
        description="Comments",
        ordering="_comment_count",
    )
    def comment_count(self, obj):
        return obj._comment_count

    actions = ["publish_selected", "move_to_drafts"]

    @admin.action(
        description="Publish selected",
        permissions=["change"],
    )
    def publish_selected(self, request, queryset):
        updated = queryset.update(status="published")

        self.message_user(
            request,
            f"Published {updated} posts.",
        )

    @admin.action(
        description="Move to drafts",
        permissions=["change"],
    )

    def move_to_drafts(self, request, queryset):
        updated = queryset.update(status="draft")

        self.message_user(
            request,
            f"Moved {updated} posts to drafts.",
        )

    actions_row = ["toggle_post_status"]

    def has_publish_permission(self, request, object_id=None):
        if object_id is None:
            return self.has_change_permission(request)

        post = self.get_object(request, object_id)

        return (
            post is not None
            and self.has_change_permission(request, post)
        )

    @action(
        description="Publish / unpublish this post",
        permissions=["publish"],
        url_path="toggle-status",
    )
    def toggle_post_status(self, request, object_id):
        post = self.get_object(request, object_id)

        if post is None:
            raise Http404("Post not found")

        target_status = (
            "draft"
            if post.status == "published"
            else "published"
        )

        if request.method == "POST":
            post.status = target_status
            post.save(update_fields=["status"])

            self.message_user(
                request,
                f"Post changed to {target_status}.",
            )

            return redirect(
                reverse("admin:blog_post_changelist")
            )

        return render(
            request,
            "admin/blog/confirm_action.html",
            {
                **self.admin_site.each_context(request),
                "title": "Change post status",
                "message": (
                    f"Change '{post.title}' to {target_status}?"
                ),
                "cancel_url": reverse(
                    "admin:blog_post_changelist"
                ),
            },
        )

    actions_list = ["publish_all_drafts"]

    @action(
        description="Publish all drafts",
        icon="publish",
        permissions=["publish"],
        url_path="publish-all-drafts",
    )
    def publish_all_drafts(self, request):
        if request.method == "POST":
            updated = Post.objects.filter(
                status="draft"
            ).update(status="published")

            self.message_user(
                request,
                f"Published {updated} draft posts.",
            )

            return redirect(
                reverse("admin:blog_post_changelist")
            )

        return render(
            request,
            "admin/blog/confirm_action.html",
            {
                **self.admin_site.each_context(request),
                "title": "Publish all drafts",
                "message": (
                    "Publish every draft post in the database?"
                ),
                "cancel_url": reverse(
                    "admin:blog_post_changelist"
                ),
            },
        )

    actions_detail = ["open_comments"]

    @action(
        description="Open this post's comments",
        icon="comment",
        url_path="comments",
    )
    def open_comments(self, request, object_id):
        url = reverse("admin:blog_comment_changelist")

        query = urlencode({
            "post__id__exact": object_id,
        })

        return redirect(f"{url}?{query}")

    actions_submit_line = ["save_and_publish"]

    @action(
        description="Save & publish",
        permissions=["publish"],
    )
    def save_and_publish(self, request, obj):
        obj.status = "published"
        obj.save(update_fields=["status"])

COMMENT_PREVIEW_LENGTH = 80


@admin.register(Comment)
class CommentAdmin(ModelAdmin):
    list_display = (
        "post_title",
        "author",
        "body_preview",
        "created_at",
    )

    list_filter = (
        ("post", AutocompleteSelectFilter),
        ("author", AutocompleteSelectFilter),
        ("created_at", RangeDateTimeFilter),
    )

    list_filter_submit = True

    search_fields = (
        "body",
        "author__email",
        "post__title",
    )

    autocomplete_fields = ("post", "author")

    list_select_related = ("post", "author")

    @admin.display(
        description="Post title",
        ordering="post__title",
    )
    def post_title(self, obj):
        return obj.post.title

    @admin.display(description="Body")
    def body_preview(self, obj):
        body = obj.body

        if len(body) > COMMENT_PREVIEW_LENGTH:
            return body[:COMMENT_PREVIEW_LENGTH] + "..."

        return body