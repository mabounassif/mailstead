from django.urls import path

from notifications import views

urlpatterns = [
    path("", views.settings_page, name="notifications_settings"),
    path("preferences/", views.settings_save, name="notifications_preferences"),
    path("subscribe/", views.subscribe, name="notifications_subscribe"),
    path("unsubscribe/", views.unsubscribe, name="notifications_unsubscribe"),
    path("test/", views.test_push, name="notifications_test"),
    path("devices/<int:device_id>/remove/", views.remove_device, name="notifications_remove_device"),
]
