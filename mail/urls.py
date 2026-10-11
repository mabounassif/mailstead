from django.urls import path

from mail import views

urlpatterns = [
    path("", views.inbox, name="mail_inbox"),
    path("compose/", views.compose, name="mail_compose"),
    path("f/<str:folder>/", views.folder_view, name="mail_folder"),
    path("m/<int:copy_id>/", views.message_detail, name="mail_message"),
    path("m/<int:copy_id>/reply/", views.reply, name="mail_reply"),
    path("m/<int:copy_id>/reply-all/", views.reply_all, name="mail_reply_all"),
    path("m/<int:copy_id>/junk/", views.mark_junk, name="mail_junk"),
    path("m/<int:copy_id>/not-junk/", views.mark_not_junk, name="mail_not_junk"),
    path("m/<int:copy_id>/trash/", views.trash_message, name="mail_trash"),
    path("m/<int:copy_id>/purge/", views.purge_message, name="mail_purge"),
    path("m/<int:copy_id>/restore/", views.restore_message, name="mail_restore"),
    path("f/trash/empty/", views.empty_trash_view, name="mail_empty_trash"),
    path("m/<int:copy_id>/export/", views.export_eml, name="mail_export"),
    path(
        "m/<int:copy_id>/att/<int:attachment_id>/",
        views.download_attachment,
        name="mail_attachment",
    ),
    path("search/", views.search, name="mail_search"),
]
