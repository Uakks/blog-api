from django.contrib.auth import get_user_model

from unfold.forms import (
    UserCreationForm,
    UserChangeForm,
)

User = get_user_model()


class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = (
            "email",
            "first_name",
            "last_name",
        )


class CustomUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User
        fields = "__all__"