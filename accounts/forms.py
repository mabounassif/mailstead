from django import forms
from django.contrib.auth import get_user_model
from accounts.models import Mailbox
from django.contrib.auth.forms import AuthenticationForm, SetPasswordForm


class MailsteadAuthenticationForm(AuthenticationForm):
    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        try:
            mailbox = user.mailbox
        except Mailbox.DoesNotExist:
            return
        if mailbox.state == Mailbox.State.DISABLED:
            raise forms.ValidationError("This account has been disabled.", code="disabled")


class BootstrapSetupForm(forms.Form):
    username = forms.CharField(max_length=150)
    password1 = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput)

    def clean_username(self):
        username = self.cleaned_data["username"]
        if get_user_model().objects.filter(username=username).exists():
            raise forms.ValidationError("Username already taken.")
        return username

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("password1")
        p2 = cleaned.get("password2")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned


class RecoveryPasswordResetForm(forms.Form):
    """Lookup by username; send reset link to recovery_email."""

    username = forms.CharField(max_length=150, label="Username")

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        User = get_user_model()
        try:
            self.user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise forms.ValidationError("Unknown username.")
        if not self.user.recovery_email:
            raise forms.ValidationError("No recovery email on file for this account.")
        if not self.user.is_active:
            raise forms.ValidationError("Account is disabled.")
        return username


class SessionAwareSetPasswordForm(SetPasswordForm):
    def __init__(self, *args, request=None, **kwargs):
        self.request = request
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        user = super().save(commit=commit)
        from django.contrib.auth import update_session_auth_hash

        if self.request and self.request.user.is_authenticated and self.request.user.pk == user.pk:
            update_session_auth_hash(self.request, user)
        return user
