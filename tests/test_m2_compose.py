import pytest
from django.contrib.auth import get_user_model

from accounts.models import Mailbox
from mail.compose import reply_all_recipients
from mail.models import Folder, Message, MessageCopy


@pytest.mark.django_db
def test_reply_all_dedupes_and_reply_to():
    User = get_user_model()
    user = User.objects.create_user("u1", password="x")
    mb = Mailbox.objects.create(user=user, address="me@mail.test")
    msg = Message.objects.create(
        from_address="sender@ext.com",
        to_index="me@mail.test,other@ext.com",
        cc_index="other@ext.com",
        reply_to="reply@ext.com",
    )
    copy = MessageCopy.objects.create(message=msg, mailbox=mb, folder=Folder.INBOX)
    to_list, cc_list, bcc = reply_all_recipients(copy, mb)
    assert "reply@ext.com" in to_list
    assert "me@mail.test" not in cc_list and "me@mail.test" not in to_list
    assert len(set(cc_list)) == len(cc_list)
