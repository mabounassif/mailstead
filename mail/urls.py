from django.urls import path

from mail import views, workspace_views

urlpatterns = [
    path("", views.inbox, name="mail_inbox"),
    path("projects/", workspace_views.create_project, name="workspace_project_create"),
    path("drive/", workspace_views.drive, name="workspace_drive"),
    path("cards/", workspace_views.cards, name="workspace_cards"),
    path("cards/<int:card_id>/delete/", workspace_views.delete_card, name="workspace_card_delete"),
    path("passwords/", workspace_views.passwords, name="workspace_passwords"),
    path("passwords/<int:entry_id>/delete/", workspace_views.delete_password, name="workspace_password_delete"),
    path("agents/", workspace_views.agents, name="workspace_agents"),
    path("agents/<int:agent_id>/delete/", workspace_views.delete_agent, name="workspace_agent_delete"),
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
