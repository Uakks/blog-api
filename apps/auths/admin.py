from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.db.models import Count

from unfold.admin import ModelAdmin
from unfold.contrib.filters.admin import BooleanRadioFilter
from unfold.decorators import display
from unfold.forms import AdminPasswordChangeForm

from apps.auths.forms import (
    CustomUserCreationForm,
    CustomUserChangeForm,
)


User = get_user_model()


@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm
    change_password_form = AdminPasswordChangeForm

    list_display = (
        "user_header",
        "active_label",
        "staff_label",
        "post_count",
    )

    list_filter = (
        ("is_active", BooleanRadioFilter),
        ("is_staff", BooleanRadioFilter),
    )

    search_fields = (
        "email",
        "first_name",
        "last_name",
    )

    ordering = ("email",)

    readonly_fields = (
        "last_login",
    )

    filter_horizontal = ("groups", "user_permissions")

    fieldsets = (
        (
            "Personal info",
            {
                "classes": ("tab",),
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                    "password",
                ),
            },
        ),
        (
            "Permissions",
            {
                "classes": ("tab",),
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (
            "Important dates",
            {
                "classes": ("tab",),
                "fields": (
                    "last_login",
                    # "created_at",
                ),
            },
        ),
    )

    add_fieldsets = (
        (
            "Add user",
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                    "password1",
                    "password2",
                ),
            },
        ),
    )

    actions = ("activate_users", "deactivate_users")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)

        return queryset.annotate(
            _post_count=Count("posts", distinct=True)
        )

    @display(description="User", header=True)
    def user_header(self, obj):
        name = (
            f"{obj.first_name} {obj.last_name}".strip()
            or obj.email
        )

        initials = "".join(
            part[0].upper()
            for part in (obj.first_name, obj.last_name)
            if part.strip()
        ) or obj.email[:2].upper()

        return name, obj.email, initials

    @display(
        description="Active",
        ordering="is_active",
        label={
            "Active": "success",
            "Inactive": "danger",
        },
    )
    def active_label(self, obj):
        return "Active" if obj.is_active else "Inactive"

    @display(
        description="Staff",
        ordering="is_staff",
        label={
            "Staff": "info",
            "Regular": "warning",
        },
    )
    def staff_label(self, obj):
        return "Staff" if obj.is_staff else "Regular"

    @display(
        description="Posts",
        ordering="_post_count",
    )
    def post_count(self, obj):
        return obj._post_count

    @admin.action(description="Activate selected users")
    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)

        self.message_user(
            request,
            f"Activated {updated} users.",
        )

    @admin.action(description="Deactivate selected users")
    def deactivate_users(self, request, queryset):
        targets = queryset.filter(
            is_superuser=False
        ).exclude(pk=request.user.pk)

        updated = targets.update(is_active=False)

        self.message_user(
            request,
            f"Deactivated {updated} users.",
        )