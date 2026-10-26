import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from accounts.models import Mailbox


def _client():
    User = get_user_model()
    user = User.objects.create_user("reviewer", password="pw")
    Mailbox.objects.create(user=user, address="reviewer@mail.test")
    client = Client()
    client.post("/accounts/login/", {"username": "reviewer", "password": "pw"})
    return client


@pytest.mark.django_db
def test_review_tab_sits_between_drive_and_contacts():
    response = _client().get("/mail/")
    html = response.content.decode()
    main = html.split("workspace-rail__main", 1)[1].split("workspace-rail__extra", 1)[0]
    assert main.index("/mail/drive/") < main.index("/mail/review/") < main.index("/mail/contacts/")
    assert "rail-btn--review" in main
    assert 'data-review-link' in main
    assert 'aria-label="Review queue"' in main
    assert "shield" in main or "fill-rule" in main


@pytest.mark.django_db
def test_review_page_is_a_local_sample_queue():
    response = _client().get("/mail/review/")
    assert response.status_code == 200
    html = response.content.decode()
    assert "Needs you" in html
    assert "Loading requests" in html
    assert "Sample requests on this device." not in html
    assert "Development only" not in html
    assert "review_page.js" in html
    assert 'id="review-dialog"' in html


@pytest.mark.django_db
def test_review_page_has_no_development_reset():
    response = _client().get("/mail/review/")
    html = response.content.decode()
    assert "data-dev-reset" not in html
    assert "Reset sample requests" not in html
