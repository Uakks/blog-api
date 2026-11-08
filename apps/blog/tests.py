"""Blog API tests covering draft privacy, ownership and CRUD."""

from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.blog.models import Category, Comment, Post, Tag


User = get_user_model()
TEST_PASSWORD = "ExamplePass1234!"


class BlogApiTests(APITestCase):
    def setUp(self) -> None:
        self.author = User.objects.create_user(
            email="author@example.com",
            password=TEST_PASSWORD,
            first_name="Blog",
            last_name="Author",
        )
        self.other = User.objects.create_user(
            email="other@example.com",
            password=TEST_PASSWORD,
            first_name="Other",
            last_name="Reader",
        )
        self.staff = User.objects.create_superuser(
            email="staff@example.com",
            password=TEST_PASSWORD,
            first_name="Staff",
            last_name="Member",
        )
        self.category = Category.objects.create(name="Python", slug="python")
        self.tag = Tag.objects.create(name="Django", slug="django")
        self.published = Post.objects.create(
            title="Public article",
            slug="public-article",
            body="Public content",
            author=self.author,
            category=self.category,
            status=Post.Status.PUBLISHED,
        )
        self.draft = Post.objects.create(
            title="Private draft",
            slug="private-draft",
            body="Private content",
            author=self.author,
            status=Post.Status.DRAFT,
        )

    def test_anonymous_sees_published_but_not_drafts(self) -> None:
        response = self.client.get(reverse("post-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["slug"], "public-article")
        response = self.client.get(reverse("post-detail", args=["private-draft"]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_author_can_see_own_draft_not_others(self) -> None:
        self.client.force_authenticate(user=self.author)
        self.assertEqual(len(self.client.get(reverse("post-list")).data), 2)
        self.client.force_authenticate(user=self.other)
        self.assertEqual(len(self.client.get(reverse("post-list")).data), 1)

    def test_post_create_requires_authentication(self) -> None:
        payload = {
            "title": "New post",
            "slug": "new-post",
            "body": "Some text",
            "status": "draft",
            "category": "python",
            "tags": ["django"],
        }
        response = self.client.post(reverse("post-list"), payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.client.force_authenticate(user=self.author)
        response = self.client.post(reverse("post-list"), payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        saved = Post.objects.get(slug="new-post")
        self.assertEqual(saved.author, self.author)
        self.assertEqual(saved.category, self.category)
        self.assertEqual(list(saved.tags.all()), [self.tag])

    def test_only_owner_can_edit_post(self) -> None:
        path = reverse("post-detail", args=["public-article"])
        self.client.force_authenticate(user=self.other)
        response = self.client.patch(
            path, {"title": "Not permitted"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.client.force_authenticate(user=self.author)
        response = self.client.patch(path, {"title": "Updated"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_staff_can_create_categories_and_tags(self) -> None:
        category_url = reverse("category-list")
        tag_url = reverse("tag-list")
        response = self.client.post(category_url, {"name": "Go", "slug": "go"})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.client.force_authenticate(user=self.staff)
        response = self.client.post(category_url, {"name": "Go", "slug": "go"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response = self.client.post(tag_url, {"name": "API", "slug": "api"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_comments_require_authentication_and_are_author_scoped(self) -> None:
        url = reverse("comment-list")
        payload = {"post": "public-article", "body": "Hi"}
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.client.force_authenticate(user=self.other)
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        comment = Comment.objects.get(pk=response.data["id"])
        self.assertEqual(comment.author, self.other)
        self.client.force_authenticate(user=self.author)
        response = self.client.delete(reverse("comment-detail", args=[comment.pk]))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_comment_on_someone_elses_draft(self) -> None:
        self.client.force_authenticate(user=self.other)
        response = self.client.post(
            reverse("comment-list"), {"post": "private-draft", "body": "Hi"}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_public_comments_hide_draft_comments(self) -> None:
        Comment.objects.create(
            post=self.published, author=self.other, body="Public comment"
        )
        Comment.objects.create(
            post=self.draft, author=self.author, body="Private comment"
        )
        response = self.client.get(reverse("comment-list"))
        self.assertEqual(len(response.data), 1)
