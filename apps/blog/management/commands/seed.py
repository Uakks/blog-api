from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.utils import timezone
from faker import Faker
import random, time

from apps.blog.models import Category, Post, Tag, Comment

User = get_user_model()
fake = Faker()

DEFAULT_USERS = 20
DEFAULT_POSTS = 100
DEFAULT_COMMENTS = 500
SEED_PASSWORD = "123123123"
DAYS_IN_YEAR = 365
SECONDS_IN_DAY = 60 * 60 * 24
EDIT_PROBABILITY = 0.30
BULK_BATCH_SIZE = 500
MAX_EDIT_DAYS = 30
NO_CATEGORY_PROBABILITY = 0.1

CATEGORY_NAMES = (
    "Python", "Django", "Databases", "Backend", "Frontend",
    "Web Development", "Career", "Technology",
)
TAG_NAMES = (
    "python", "django", "orm", "database", "sql", "backend", "frontend",
    "api", "rest", "testing", "deployment", "security", "tutorial",
    "beginner", "advanced", "performance", "web", "career", "async", "tips",
)


def assign_post_dates(posts: list[Post], now):
    for post in posts:
        seconds_ago  = random.randint(0, DAYS_IN_YEAR * SECONDS_IN_DAY)
        post.created_at = now - timedelta(seconds=seconds_ago)
        post.updated_at = post.created_at

        if random.random() < EDIT_PROBABILITY:
            days_available = min(MAX_EDIT_DAYS, seconds_ago // SECONDS_IN_DAY)
            if days_available >= 1:
                post.updated_at = post.created_at + timedelta(days=random.randint(1, days_available))

    if posts:
        Post.objects.bulk_update(posts, ["created_at", "updated_at"], batch_size=BULK_BATCH_SIZE)

def assign_comment_dates(comments: list[Comment], now):
    for comment in comments:
        earliest = comment.post.created_at
        span_secs = max(0, int((now - earliest).total_seconds()))
        comment.created_at = earliest + timedelta(seconds=random.randint(0, span_secs))
    if comments:
        Comment.objects.bulk_update(comments, ["created_at"], batch_size=BULK_BATCH_SIZE)
        


class Command(BaseCommand):
    help = "Fill the database with fake data."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--users", type=int, default=DEFAULT_USERS, help="Number of users to create")
        parser.add_argument("--posts", type=int, default=DEFAULT_POSTS, help="Number of posts to create")
        parser.add_argument("--comments", type=int, default=DEFAULT_COMMENTS, help="Number of comments to create")
        parser.add_argument("--clear", action="store_true", help="Delete existing data before seeding")

    def handle(self, *args, **options):
        start_time = time.perf_counter()

        users = options["users"]
        posts = options["posts"]
        comments = options["comments"]
        clear = options["clear"]

        Category.objects.bulk_create(
            [Category(name=n, slug=slugify(n)) for n in CATEGORY_NAMES],
            ignore_conflicts=True
        )
        Tag.objects.bulk_create(
            [Tag(name=n, slug=slugify(n)) for n in TAG_NAMES],
            ignore_conflicts=True
        )
        categories = list[Category.objects.all()]
        tags = list[Tag.objects.all()]

        if users < 0:
            raise CommandError("--users must be not negative")
        else:
            created_users = []
            for i in range(users):
                user = User(
                    first_name = fake.first_name(),
                    last_name = fake.last_name(),
                    email = f"{fake.unique.email()}",
                    is_active = random.randint(0, 1) == 1,
                    is_staff = random.randint(0, 1) == 1,
                )
                user.set_password(SEED_PASSWORD)
                created_users.append(user)

            User.objects.bulk_create(created_users)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Users: {users} created"
                )
            )

        all_users = list(User.objects.all())
        categories = list(Category.objects.all())
        tags = list(Tag.objects.all())

        now = timezone.now()

        if posts < 0:
            raise CommandError("--posts must be not negative")
        else:
            if not all_users and posts > 0:
                raise ValueError("No users exist for created posts")

            created_posts = []
            post_tags = []
            existing_slugs = set(
                Post.objects.values_list("slug", flat=True)
            )
            for i in range(posts):
                cur_title = fake.sentence(nb_words=3).title()
                base_slug = slugify(cur_title)
                cur_slug = base_slug
                counter = 2

                while cur_slug in existing_slugs:
                    cur_slug = f"{base_slug}-{counter}"
                    counter += 1
                existing_slugs.add(cur_slug)
                post = Post(
                    author = random.choice(all_users),
                    title = cur_title,
                    body = fake.text(max_nb_chars=300),
                    slug = cur_slug,
                    status = "published" if random.random() < 0.7 else "draft",
                    category = (random.choice(categories)
                                if categories and random.random() >= NO_CATEGORY_PROBABILITY
                                else None),
                )

                selected_tags = random.sample(
                    tags,
                    k=random.randint(0, min(5, len(tags)))
                )
                post_tags.append(selected_tags)
                created_posts.append(post)

            Post.objects.bulk_create(created_posts)
            assign_post_dates(created_posts, now)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Posts: {posts} created"
                )
            )
            for post, selected_tags in zip(created_posts, post_tags):
                post.tags.set(selected_tags)

        published_posts = list(Post.objects.all().filter(status="published"))

        if comments < 0:
            raise CommandError("--comments must be not negative")
        else:
            if (len(all_users) == 0 or len(published_posts) == 0) and comments > 0:
                raise ValueError("no users or published posts for comments")
            created_comments = []
            for i in range(comments):
                comment = Comment(
                    post = random.choice(published_posts),
                    author = random.choice(all_users),
                    body = fake.sentences(nb=3)
                )

            created_comments.append(comment)
            Comment.objects.bulk_create(created_comments)
            assign_comment_dates(created_comments, now)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Comments: {comments} created"
                )
            )

        if clear:
            User.objects.filter(is_superuser=False).delete()
            Post.objects.all().delete()
            Comment.objects.all().delete()
            self.stdout.write(
                self.style.SUCCESS(
                    f"Database cleared"
                )
            )

        end_time = time.perf_counter()
        self.stdout.write(
            self.style.SUCCESS(
                f"Done in {start_time - end_time:.2f} seconds"
            )
        )
        # self.stdout.write(
        #     self.style.SUCCESS(
        #         f"{len(list(User.objects.all()))}"
        #     )
        # )