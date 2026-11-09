from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from faker import Faker
import random, time

from apps.blog.models import Category, Post, Tag, Comment

User = get_user_model()
fake = Faker()

DEFAULT_USERS = 20
DEFAULT_POSTS = 100
DEFAULT_COMMENTS = 500
SEED_PASSWORD = "123123123"

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

        cur_category = None
        if categories and random.random() >= 0.1:
            cur_category = random.choice(categories)

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
                    category = cur_category,
                )

                selected_tags = random.sample(
                    tags,
                    k=random.randint(0, min(5, len(tags)))
                )
                post_tags.append(selected_tags)
                created_posts.append(post)

            Post.objects.bulk_create(created_posts)
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
            self.style.SUCCESS(f"Created {comments} comments")
            self.stdout.write(
                self.style.SUCCESS(
                    f"Comments: {comments} created"
                )
            )

        if clear:
            User.objects.filter(is_superuser=False).delete()
            Post.objects.all().delete()
            Comment.objects.all().delete()

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