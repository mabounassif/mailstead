from django.urls import path

from storage import views

urlpatterns = [
    path("", views.ops_dashboard, name="ops_dashboard"),
]
