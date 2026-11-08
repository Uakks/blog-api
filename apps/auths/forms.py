"""Admin forms compatible with AbstractBaseUser."""

from django import forms
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.contrib.auth.password_validation import validate_password

from apps.auths.models import User


class CustomUserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirm password", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ("email", "first_name", "last_name")

    def clean_password2(self) -> str:
        first = self.cleaned_data.get("password1")
        second = self.cleaned_data.get("password2")
        if first != second:
            raise forms.ValidationError("Passwords do not match.")
        validate_password(second)
        return second

    def save(self, commit: bool = True) -> User:
        user: User = super().save(commit=False)
        user.email = User.objects.normalize_email(user.email).lower()
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
            self.save_m2m()
        return user


class CustomUserChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = User
        fields = (
            "email", "first_name", "last_name", "password", "is_active", "is_staff"
        )
