from __future__ import annotations
from datetime import timedelta
from typing import Any

from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.db import connection
from django.db.models import Count, Model, QuerySet
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from apps.auths.models import User
from apps.blog import queries
from apps.blog.models import Category, Post, Tag, Comment

MUTATING_QUERIES = frozenset({40, 41, 42, 43, 44})
SAMPLE_PAGE = 1
SAMPLE_DAYS = 30
SAMPLE_MIN_POSTS = 2
SAMPLE_TAG_NAME = "Django ORM"
FALLBACK_EMAIL = "example@mail.ru"
FALLBACK_SLUG = "django"
PREVIEW_LIMIT = 5

SAMPLE_ARGUMENTS: dict[int, dict[str, Any]] = {
    7: {"page": SAMPLE_PAGE},
    13: {"days": SAMPLE_DAYS},
    34: {"min_posts": SAMPLE_MIN_POSTS},
    40: {"name": SAMPLE_TAG_NAME},
    41: {"days": SAMPLE_DAYS},
}

def sample_arguments(number: int) -> dict[str, Any]:
    arguments = dict(SAMPLE_ARGUMENTS.get(number, {}))

    if number in {4, 8, 22}:
        post = Post.objects.values("slug", "title").first()
        slug = post["slug"] if post else "missing-post"
        word = post["title"].split()[0] if post and post["title"].split() else "Django"
        if number == 4:
            arguments["slug"] = 4
        else:
            arguments["word" if number == 8 else "text"] = word
    elif number == 9:
        email = User.objects.values_list("email", flat=True).first() or FALLBACK_EMAIL
        arguments["domain"] = email.partition("@")[2] or "mail.ru"
    elif number == 11:
        arguments["slugs"] = list(Category.objects.values_list("slug", flat=True)[:2])
    elif number == 12:
        created = Post.objects.values_list("created_at", flat=True).first() or timezone.now()
        arguments.update(year=created.year, month = created.month)
    elif number == 14:
        today = timezone.localdate()
        arguments.update(start=today - timedelta(days=365), end=today)
    elif number == 15:
        arguments["email"] = (
            Post.objects.filter(status=Post.Status.PUBLISHED).values_list("author__email", flat=True).first()
            or FALLBACK_EMAIL
        )
    elif number in {16, 42}:
        arguments["tag_slug"] = (
            Post.objects.filter(tags__isnull=False).values_list("tags__slug", flat=True).first()
            or Tag.objects.values_list("slug", flat=True).first()
            or FALLBACK_SLUG
        )
        if number == 42:
            arguments["category_slug"] = (
                Category.objects.filter(posts__isnull=False).values_list("slug", flat=True).first()
                or FALLBACK_SLUG
            )
    elif number == 17:
        arguments["category_slug"] = (
            Comment.objects.filter(post__category__isnull=False).values_list("post__category__slug", flat=True).first()
            or FALLBACK_SLUG
        )
    elif number == 21:
        post = Post.objects.annotate(tag_count=Count("tags")).filter(tag_count__gte=2).first()
        slugs = list(post.tags.values_list("slug", flat=True)[:2]) if post else []
        arguments.update(
            first_slug=slugs[0] if slugs else FALLBACK_SLUG,
            second_slug=slugs[1] if len(slugs) > 1 else FALLBACK_SLUG
        )
    elif number == 37:
        user = User.objects.values("first_name", "last_name").first()
        arguments["text"] = user["first_name"] if user else "Uali"
    elif number == 43:
        source = (
            Category.objects.filter(posts__isnull=False).values_list("slug", flat=True).first()
            or FALLBACK_SLUG
        )
        target = (
            Category.objects.exclude(slug=source).values_list("slug", flat=True).first()
            or source
        )
        arguments.update(source_slug=source, target_slug=target)
    return arguments
        
    
def show_row(row: Any, annotations: tuple[str, ...] = ()) -> str:
    if isinstance(row, Model):
        extras = {name: getattr(row, name) for name in annotations}
        return f"{row} {extras}" if extras else str(row)
    return str(row)

class Command(BaseCommand):
    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--number", type=int, help="Run one numbered query (1-50)")
        parser.add_argument("--sql", action="store_true", help="Print executed sql statements")

    def handle(self, *args, **options):
        number = options["number"]
        if number is not None and number not in queries.QUERIES:
            raise CommandError(f"Unknown query number: {number}")

        numbers = (
            [number] 
            if number is not None 
            else [n for n in queries.QUERIES if n not in MUTATING_QUERIES]
        )

        for query_number in numbers:
            self.run_one(query_number, show_sql=options["sql"])

    def run_one(self, number: int, show_sql: bool):
        function = queries.QUERIES[number]
        arguments = sample_arguments(number)
        annotations: tuple[str, ...] = ()

        with CaptureQueriesContext(connection) as captured:
            result = function(**arguments)
            if isinstance(result, QuerySet):
                annotations = tuple(result.query.annotations)
                result = list(result)

        count = len(captured.captured_queries)
        suffix = "query" if count == 1 else "queries"
        self.stdout.write(f"#{number} {function.__name__} - {count} SQL {suffix}")
        if show_sql:
            for statement in captured.captured_queries:
                self.stdout.write(statement["sql"])

        if isinstance(result, list):
            for row in result[:PREVIEW_LIMIT]:
                self.stdout.write(f"  {show_row(row, annotations)}")
            self.stdout.write(f"  ({len(result)} rows)")
        else:
            self.stdout.write(f"  {show_row(result, annotations)}")
            
                