from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from django.db import transaction
from django.db.models import (
    Avg,
    Case,
    CharField,
    Count,
    Exists,
    F,
    Max,
    Min,
    OuterRef,
    Q,
    QuerySet,
    Subquery,
    Value,
    When,
)
from django.db.models.functions import Coalesce, Concat, TruncMonth
from django.utils import timezone
from django.utils.text import slugify

from apps.auths.models import User
from apps.blog.models import Category, Comment, Post, Tag

PAGE_SIZE = 10
NEWEST_POSTS_LIMIT = 5
TOP_AUTHORS_LIMIT = 5
FEED_SIZE = 50
TAG_FEED_SIZE = 20
EDIT_THRESHOLD = timedelta(hours=1)
HOT_COMMENTS = 10
NORMAL_COMMENTS = 3
UNCATEGORIZED = "Uncategorized"
HOT = "hot"
NORMAL = "normal"
QUIET = "quiet"


# Level 1: First queries

def categories_by_name() -> QuerySet[Category]:
    """Return categories alphabetically."""
    return Category.objects.order_by("name")


def published_posts() -> QuerySet[Post]:
    """Return newest published posts first."""
    return Post.objects.filter(status=Post.Status.PUBLISHED).order_by("-created_at", "-pk")


def newest_published_posts() -> QuerySet[Post]:
    """Return the five newest published posts."""
    return published_posts()[:NEWEST_POSTS_LIMIT]


def post_by_slug(slug: str) -> Post | None:
    """Find a post, or None if its slug is missing."""
    return Post.objects.filter(slug=slug).first()


def active_users_count() -> int:
    """Count non-staff active users."""
    return User.objects.filter(is_active=True, is_staff=False).count()


def has_drafts() -> bool:
    """Check whether at least one draft exists."""
    return Post.objects.filter(status=Post.Status.DRAFT).exists()


def published_posts_page(page: int) -> QuerySet[Post]:
    """Return a one-indexed page of ten published posts."""
    start = (page - 1) * PAGE_SIZE
    return published_posts()[start : start + PAGE_SIZE]


# Level 2: Field lookups

def posts_with_word_in_title(word: str) -> QuerySet[Post]:
    """Find titles containing a word regardless of case."""
    return Post.objects.filter(title__icontains=word)


def users_with_email_domain(domain: str) -> QuerySet[User]:
    """Find users whose email ends with @domain."""
    return User.objects.filter(email__iendswith=f"@{domain}")


def posts_without_category() -> QuerySet[Post]:
    """Find posts with a null category."""
    return Post.objects.filter(category__isnull=True)


def categories_by_slugs(slugs: list[str]) -> QuerySet[Category]:
    """Find categories matching any supplied slug."""
    return Category.objects.filter(slug__in=slugs)


def posts_in_month(year: int, month: int) -> QuerySet[Post]:
    """Find posts created in the given year and month."""
    return Post.objects.filter(created_at__year=year, created_at__month=month)


def posts_last_days(days: int) -> QuerySet[Post]:
    """Find posts from the last number of days."""
    return Post.objects.filter(created_at__gte=timezone.now() - timedelta(days=days))


def posts_between(start: date, end: date) -> QuerySet[Post]:
    """Include posts created on both boundary dates."""
    return Post.objects.filter(created_at__date__range=(start, end))


# Level 3: Queries across relations

def author_published_posts(email: str) -> QuerySet[Post]:
    """Find an author's published posts using case-insensitive email."""
    return Post.objects.filter(
        author__email__iexact=email,
        status=Post.Status.PUBLISHED,
    )


def posts_with_tag(tag_slug: str) -> QuerySet[Post]:
    """Find posts with a given tag slug."""
    return Post.objects.filter(tags__slug=tag_slug)


def comments_in_category(category_slug: str) -> QuerySet[Comment]:
    """Find comments on posts belonging to a category."""
    return Comment.objects.filter(post__category__slug=category_slug)


def users_with_published_posts() -> QuerySet[User]:
    """Find distinct users with at least one published post."""
    return User.objects.filter(posts__status=Post.Status.PUBLISHED).distinct()


def posts_without_tags() -> QuerySet[Post]:
    """Find posts with no tags."""
    return Post.objects.filter(tags__isnull=True)


def users_without_comments() -> QuerySet[User]:
    """Find users who have written no comments."""
    return User.objects.filter(comments__isnull=True)


def posts_with_both_tags(first_slug: str, second_slug: str) -> QuerySet[Post]:
    """Find posts carrying both specified tags."""
    return (
        Post.objects.filter(tags__slug=first_slug)
        .filter(tags__slug=second_slug)
        .distinct()
    )


# Level 4: Q and F

def search_posts(text: str) -> QuerySet[Post]:
    """Search text in title OR body."""
    return Post.objects.filter(Q(title__icontains=text) | Q(body__icontains=text))


def published_posts_missing_info() -> QuerySet[Post]:
    """Find published posts without a category OR without tags."""
    return Post.objects.filter(status=Post.Status.PUBLISHED).filter(
        Q(category__isnull=True) | Q(tags__isnull=True)
    ).distinct()


def edited_posts() -> QuerySet[Post]:
    """Find posts modified more than one hour after creation."""
    return Post.objects.filter(updated_at__gt=F("created_at") + EDIT_THRESHOLD)


def comments_by_post_author() -> QuerySet[Comment]:
    """Find comments made by the post's own author."""
    return Comment.objects.filter(author_id=F("post__author_id"))


def comments_before_post() -> QuerySet[Comment]:
    """Find invalid comments that predate their posts."""
    return Comment.objects.filter(created_at__lt=F("post__created_at"))


# Level 5: values and values_list

def published_authors_emails() -> list[str]:
    """Return sorted, unique published-author email strings."""
    return list(
        Post.objects.filter(status=Post.Status.PUBLISHED)
        .order_by("author__email")
        .values_list("author__email", flat=True)
        .distinct()
    )


def published_posts_overview() -> list[dict[str, Any]]:
    """Return three projected fields per published post."""
    return list(
        Post.objects.filter(status=Post.Status.PUBLISHED)
        .annotate(
            author_email=F("author__email"),
            category_name=Coalesce("category__name", Value(UNCATEGORIZED)),
        )
        .values("title", "author_email", "category_name")
    )


# Level 6: aggregate

def posts_stats() -> dict[str, Any]:
    """Calculate all post counts and first/last dates in one query."""
    return Post.objects.aggregate(
        total=Count("id"),
        published=Count("id", filter=Q(status=Post.Status.PUBLISHED)),
        drafts=Count("id", filter=Q(status=Post.Status.DRAFT)),
        first_post_at=Min("created_at"),
        last_post_at=Max("created_at"),
    )


def average_comments_per_post() -> float:
    """Average comment count for published posts, including zero comments."""
    result = (
        Post.objects.filter(status=Post.Status.PUBLISHED)
        .annotate(comment_count=Count("comments"))
        .aggregate(average=Avg("comment_count"))
    )
    return round(result["average"] or 0.0, 2)


# Level 7: annotate

def categories_with_post_count() -> QuerySet[Category]:
    """Count posts in each category and order by popularity."""
    return Category.objects.annotate(
        post_count=Count("posts", distinct=True)
    ).order_by("-post_count", "name")


def categories_with_published_count() -> QuerySet[Category]:
    """Count published posts, keeping categories with zero matches."""
    return Category.objects.annotate(
        published_count=Count(
            "posts", filter=Q(posts__status=Post.Status.PUBLISHED), distinct=True
        )
    )


def top_authors() -> QuerySet[User]:
    """Return the five authors with the most published posts."""
    return User.objects.annotate(
        published_count=Count(
            "posts", filter=Q(posts__status=Post.Status.PUBLISHED), distinct=True
        )
    ).order_by("-published_count", "email")[:TOP_AUTHORS_LIMIT]


def popular_tags(min_posts: int) -> QuerySet[Tag]:
    """Find tags appearing in at least min_posts posts."""
    return Tag.objects.annotate(
        post_count=Count("posts", distinct=True)
    ).filter(post_count__gte=min_posts).order_by("-post_count", "name")


def posts_per_status() -> list[dict[str, Any]]:
    """Return one status/count dictionary for each status."""
    return list(
        Post.objects.order_by()
        .values("status")
        .annotate(count=Count("id"))
        .order_by("status")
    )


def users_activity() -> QuerySet[User]:
    """Annotate accurate post and comment counts per user."""
    return User.objects.annotate(
        post_count=Count("posts", distinct=True),
        comment_count=Count("comments", distinct=True),
    )


# Level 8: Database functions and conditions

def search_users_by_full_name(text: str) -> QuerySet[User]:
    """Search a concatenated first + last name in SQL."""
    return User.objects.annotate(
        full_name=Concat("first_name", Value(" "), "last_name")
    ).filter(full_name__icontains=text)


def published_posts_per_month() -> list[dict[str, Any]]:
    """Count published posts by month, oldest month first."""
    return list(
        Post.objects.filter(status=Post.Status.PUBLISHED)
        .order_by()
        .annotate(month=TruncMonth("created_at"))
        .values("month")
        .annotate(count=Count("id"))
        .order_by("month")
    )


def posts_with_popularity() -> QuerySet[Post]:
    """Mark each post hot, normal, or quiet based on its comments."""
    return Post.objects.annotate(
        comment_count=Count("comments", distinct=True)
    ).annotate(
        popularity=Case(
            When(comment_count__gte=HOT_COMMENTS, then=Value(HOT)),
            When(comment_count__gte=NORMAL_COMMENTS, then=Value(NORMAL)),
            default=Value(QUIET),
            output_field=CharField(),
        )
    )


# Level 9: Changing data (run one at a time)

def get_or_create_tag(name: str) -> tuple[Tag, bool]:
    """Get a tag by its unique normalized slug or create it."""
    return Tag.objects.get_or_create(slug=slugify(name), defaults={"name": name})


def publish_old_drafts(days: int) -> int:
    """Publish old drafts using a single UPDATE statement."""
    now = timezone.now()
    return Post.objects.filter(
        status=Post.Status.DRAFT,
        created_at__lt=now - timedelta(days=days),
    ).update(status=Post.Status.PUBLISHED, updated_at=now)


def tag_category_posts(category_slug: str, tag_slug: str) -> int:
    """Tag all posts in a category without duplicating M2M links."""
    tag = Tag.objects.get(slug=tag_slug)
    post_ids = list(
        Post.objects.filter(category__slug=category_slug).values_list("pk", flat=True)
    )
    tag.posts.add(*post_ids)
    return len(post_ids)


def merge_categories(source_slug: str, target_slug: str) -> int:
    """Move posts to another category and remove the source atomically."""
    with transaction.atomic():
        source = Category.objects.get(slug=source_slug)
        target = Category.objects.get(slug=target_slug)
        if source.pk == target.pk:
            return 0
        moved = Post.objects.filter(category=source).update(category=target)
        source.delete()
        return moved


def delete_inactive_users_comments() -> int:
    """Delete comments authored by inactive users."""
    deleted, _ = Comment.objects.filter(author__is_active=False).delete()
    return deleted


# Level 10: select_related and prefetch_related

def published_feed() -> list[str]:
    """Format 50 newest published posts using one SELECT query."""
    posts = (
        Post.objects.filter(status=Post.Status.PUBLISHED)
        .select_related("author", "category")
        .order_by("-created_at", "-pk")[:FEED_SIZE]
    )
    return [
        f"{post.title} | {post.author.email} | "
        f"{post.category.name if post.category else UNCATEGORIZED}"
        for post in posts
    ]


def newest_posts_with_tags() -> list[str]:
    """Format posts and prefetched tag names in at most two queries."""
    posts = Post.objects.order_by("-created_at", "-pk").prefetch_related("tags")[
        :TAG_FEED_SIZE
    ]
    return [
        f"{post.title}: {', '.join(tag.name for tag in post.tags.all())}"
        for post in posts
    ]


def categories_with_published_posts() -> dict[str, list[str]]:
    """Prefetch only published posts, newest first, for every category."""
    from django.db.models import Prefetch

    categories = Category.objects.prefetch_related(
        Prefetch(
            "posts",
            queryset=Post.objects.filter(status=Post.Status.PUBLISHED).order_by(
                "-created_at", "-pk"
            ),
            to_attr="published_posts",
        )
    )
    return {
        category.name: [post.title for post in category.published_posts]
        for category in categories
    }


# Level 11: Subquery and Exists

def posts_with_last_comment() -> QuerySet[Post]:
    """Annotate the body of the latest comment per published post."""
    latest_comment = (
        Comment.objects.filter(post_id=OuterRef("pk"))
        .order_by("-created_at", "-pk")
        .values("body")[:1]
    )
    return Post.objects.filter(status=Post.Status.PUBLISHED).annotate(
        last_comment=Subquery(latest_comment)
    )


def posts_with_staff_comments() -> QuerySet[Post]:
    """Find posts having at least one comment by a staff user."""
    staff_comments = Comment.objects.filter(
        post_id=OuterRef("pk"), author__is_staff=True
    )
    return Post.objects.filter(Exists(staff_comments))


def users_with_draft_as_latest_post() -> QuerySet[User]:
    """Find users whose newest post's status is draft."""
    latest_post = (
        Post.objects.filter(author_id=OuterRef("pk"))
        .order_by("-created_at", "-pk")
        .values("status")[:1]
    )
    return User.objects.annotate(
        latest_post_status=Subquery(latest_post)
    ).filter(latest_post_status=Post.Status.DRAFT)


# Required registry: function names and numbers are fixed by Homework 3.
QUERIES = {
    1: categories_by_name,
    2: published_posts,
    3: newest_published_posts,
    4: post_by_slug,
    5: active_users_count,
    6: has_drafts,
    7: published_posts_page,
    8: posts_with_word_in_title,
    9: users_with_email_domain,
    10: posts_without_category,
    11: categories_by_slugs,
    12: posts_in_month,
    13: posts_last_days,
    14: posts_between,
    15: author_published_posts,
    16: posts_with_tag,
    17: comments_in_category,
    18: users_with_published_posts,
    19: posts_without_tags,
    20: users_without_comments,
    21: posts_with_both_tags,
    22: search_posts,
    23: published_posts_missing_info,
    24: edited_posts,
    25: comments_by_post_author,
    26: comments_before_post,
    27: published_authors_emails,
    28: published_posts_overview,
    29: posts_stats,
    30: average_comments_per_post,
    31: categories_with_post_count,
    32: categories_with_published_count,
    33: top_authors,
    34: popular_tags,
    35: posts_per_status,
    36: users_activity,
    37: search_users_by_full_name,
    38: published_posts_per_month,
    39: posts_with_popularity,
    40: get_or_create_tag,
    41: publish_old_drafts,
    42: tag_category_posts,
    43: merge_categories,
    44: delete_inactive_users_comments,
    45: published_feed,
    46: newest_posts_with_tags,
    47: categories_with_published_posts,
    48: posts_with_last_comment,
    49: posts_with_staff_comments,
    50: users_with_draft_as_latest_post,
}
