from django.urls import path

from enterprise import views

urlpatterns = [
    path("", views.enterprise_page, name="enterprise_page"),
]
