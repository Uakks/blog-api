import os
import json

from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from apps.blog.models import Category, Comment, Post
from django.urls import reverse_lazy



def environment_callback(request):
    env = os.getenv("BLOG_ENV_ID", "local")

    if env == "production":
        return ["Production", "danger"]

    return ["Local", "warning"]


def draft_posts_badge(request):
    return Post.objects.filter(status="draft").count()


def sidebar_navigation(request):
    navigation = [
        {
            "title": "Overview",
            "separator": True,
            "items": [
                {
                    "title": "Dashboard",
                    "icon": "dashboard",
                    "link": reverse_lazy("admin:index"),
                },
            ],
        },
        {
            "title": "Content",
            "separator": True,
            "items": [
                {
                    "title": "Posts",
                    "icon": "article",
                    "link": reverse_lazy(
                        "admin:blog_post_changelist"
                    ),
                    "badge": (
                        "apps.blog.admin_callbacks."
                        "draft_posts_badge"
                    ),
                    "badge_variant": "warning",
                },
                {
                    "title": "Comments",
                    "icon": "comment",
                    "link": reverse_lazy(
                        "admin:blog_comment_changelist"
                    ),
                },
                {
                    "title": "Categories",
                    "icon": "category",
                    "link": reverse_lazy(
                        "admin:blog_category_changelist"
                    ),
                },
                {
                    "title": "Tags",
                    "icon": "sell",
                    "link": reverse_lazy(
                        "admin:blog_tag_changelist"
                    ),
                },
            ],
        },
    ]

    if request.user.is_superuser:
        navigation.append(
            {
                "title": "Users & Access",
                "separator": True,
                "items": [
                    {
                        "title": "Users",
                        "icon": "people",
                        "link": reverse_lazy(
                            "admin:auths_user_changelist"
                        ),
                    },
                    {
                        "title": "Groups",
                        "icon": "groups",
                        "link": reverse_lazy(
                            "admin:auth_group_changelist"
                        ),
                    },
                ],
            }
        )

    return navigation


User = get_user_model()

def dashboard_callback(request, context):
    # 1. Statistics for cards
    total_users = User.objects.count()
    total_comments = Comment.objects.count()

    post_stats = Post.objects.aggregate(
        total=Count("id"),
        published=Count(
            "id",
            filter=Q(status="published"),
        ),
        drafts=Count(
            "id",
            filter=Q(status="draft"),
        ),
    )

    total_posts = post_stats["total"]
    published = post_stats["published"]
    drafts = post_stats["drafts"]

    cards = [
        {"title": "Total users", "value": total_users},
        {"title": "Published posts", "value": published},
        {"title": "Draft posts", "value": drafts},
        {"title": "Comments", "value": total_comments},
    ]

    # 2. Posts per category
    category_counts = {
        item["category_id"]: item["total"]
        for item in (
            Post.objects
            .values("category_id")
            .annotate(total=Count("id"))
        )
    }

    categories = Category.objects.values(
        "id", "name"
    ).order_by("name")

    labels = []
    values = []

    for category in categories:
        labels.append(category["name"])
        values.append(
            category_counts.get(category["id"], 0)
        )

    if None in category_counts:
        labels.append("Uncategorized")
        values.append(category_counts[None])

    posts_chart = json.dumps({
        "labels": labels,
        "datasets": [
            {
                "label": "Posts",
                "data": values,
                "backgroundColor": "#2563eb",
                "displayYAxis": True,
            }
        ],
    })

    # 3. Top 5 authors
    top_authors = (
        Post.objects
        .values(
            "author__email",
            "author__first_name",
            "author__last_name",
        )
        .annotate(post_count=Count("id"))
        .order_by("-post_count", "author__email")[:5]
    )

    author_rows = []

    for author in top_authors:
        full_name = (
            f"{author['author__first_name']} "
            f"{author['author__last_name']}"
        ).strip()

        author_rows.append([
            full_name or author["author__email"],
            author["author__email"],
            author["post_count"],
        ])

    authors_table = {
        "headers": ["Author", "Email", "Posts"],
        "rows": author_rows,
    }

    # 4. Published vs draft percentages
    published_pct = (
        round(published / total_posts * 100, 1)
        if total_posts else 0
    )

    draft_pct = (
        round(drafts / total_posts * 100, 1)
        if total_posts else 0
    )

    # Pass everything to the dashboard template
    context.update({
        "cards": cards,
        "posts_chart": posts_chart,
        "authors_table": authors_table,
        "published_pct": published_pct,
        "draft_pct": draft_pct,
        "published_description": (
            f"{published} of {total_posts} posts "
            f"({published_pct}%)"
        ),
        "draft_description": (
            f"{drafts} of {total_posts} posts "
            f"({draft_pct}%)"
        ),
    })

    return context

