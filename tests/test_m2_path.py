import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from accounts.models import Mailbox


@pytest.mark.django_db
def test_path_traversal_blob_rejected():
    User = get_user_model()
    user = User.objects.create_user("u1", password="x")
    Mailbox.objects.create(user=user, address="a@mail.test")
    client = Client()
    client.post("/accounts/login/", {"username": "u1", "password": "x"})
    resp = client.get("/mail/blob/not-a-sha256/")
    assert resp.status_code == 404
