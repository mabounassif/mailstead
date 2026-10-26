from __future__ import annotations

import logging

from django.contrib import messages
from django.contrib.auth.views import LoginView, PasswordResetConfirmView
from django.contrib.auth.views import PasswordResetDoneView as DjangoPasswordResetDoneView
from django.http import HttpRequest, HttpResponse, HttpResponseForbidden
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View

from accounts.forms import (
    BootstrapSetupForm,
    MailsteadAuthenticationForm,
    RecoveryPasswordResetForm,
    SessionAwareSetPasswordForm,
)
from accounts.password_reset import send_password_reset
from accounts.throttles import password_reset_hit, password_reset_throttled
from core.bootstrap import consume_bootstrap, verify_setup_token

logger = logging.getLogger(__name__)


class UserLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = MailsteadAuthenticationForm

    def get_success_url(self) -> str:
        return reverse("mail_inbox")


class SetupView(View):
    template_name = "accounts/setup.html"

    def get(self, request: HttpRequest, token: str) -> HttpResponse:
        if not verify_setup_token(token):
            return HttpResponseForbidden("Invalid or expired setup link.")
        return render(request, self.template_name, {"form": BootstrapSetupForm(), "token": token})

    def post(self, request: HttpRequest, token: str) -> HttpResponse:
        if not verify_setup_token(token):
            return HttpResponseForbidden("Invalid or expired setup link.")
        form = BootstrapSetupForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form, "token": token})
        try:
            consume_bootstrap(form.cleaned_data["username"], form.cleaned_data["password1"])
        except ValueError:
            return HttpResponseForbidden("Setup already completed.")
        messages.success(request, "Administrator account created. Please sign in.")
        return redirect("login")


class PasswordResetRequestView(View):
    template_name = "accounts/password_reset.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        return render(request, self.template_name, {"form": RecoveryPasswordResetForm()})

    def post(self, request: HttpRequest) -> HttpResponse:
        if password_reset_throttled(request):
            messages.error(request, "Too many reset requests. Try again later.")
            return render(request, self.template_name, {"form": RecoveryPasswordResetForm()})

        form = RecoveryPasswordResetForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form})

        password_reset_hit(request)
        send_password_reset(form.user)
        return redirect("password_reset_done")


class MailsteadPasswordResetConfirmView(PasswordResetConfirmView):
    form_class = SessionAwareSetPasswordForm
    template_name = "accounts/password_reset_confirm.html"
    success_url = "/accounts/login/"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        from accounts.session_utils import invalidate_user_sessions

        invalidate_user_sessions(
            self.user.pk,
            except_session_key=self.request.session.session_key if self.request.user.is_authenticated else None,
        )
        from api.auth import revoke_api_tokens

        revoke_api_tokens(self.user)
        return response


class PasswordResetDoneView(DjangoPasswordResetDoneView):
    template_name = "accounts/password_reset_done.html"
