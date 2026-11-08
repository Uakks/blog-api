"""Basic REST endpoints for posts, comments, categories and tags."""

from rest_framework import permissions, viewsets

from django.db.models import Q, QuerySet

from apps.blog.models import Category, Comment, Post, Tag
from apps.blog.permissions import IsOwnerOrReadOnly, IsStaffOrReadOnly
from apps.blog.serializers import (
    CategorySerializer,
    CommentSerializer,
    PostSerializer,
    TagSerializer,
)


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = (IsStaffOrReadOnly,)
    lookup_field = "slug"


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (IsStaffOrReadOnly,)
    lookup_field = "slug"


class PostViewSet(viewsets.ModelViewSet):
    serializer_class = PostSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly)
    lookup_field = "slug"

    def get_queryset(self) -> QuerySet[Post]:
        posts = Post.objects.select_related("author", "category").prefetch_related(
            "tags"
        )
        user = self.request.user
        if not user.is_authenticated:
            return posts.filter(status=Post.Status.PUBLISHED)
        if user.is_staff:
            return posts
        return posts.filter(Q(status=Post.Status.PUBLISHED) | Q(author=user))

    def perform_create(self, serializer: PostSerializer) -> None:
        serializer.save(author=self.request.user)


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly)

    def get_queryset(self) -> QuerySet[Comment]:
        comments = Comment.objects.select_related("author", "post")
        user = self.request.user
        if not user.is_authenticated:
            return comments.filter(post__status=Post.Status.PUBLISHED)
        if user.is_staff:
            return comments
        return comments.filter(
            Q(post__status=Post.Status.PUBLISHED) | Q(post__author=user)
        )

    def perform_create(self, serializer: CommentSerializer) -> None:
        serializer.save(author=self.request.user)
