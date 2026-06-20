from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

app_name = "monitoring"

urlpatterns = [
    path("", views.landing, name="landing"),
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="login.html",
            redirect_authenticated_user=True,
        ),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("app/", views.home, name="home"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("profile/", views.profile, name="profile"),
    path("resources/", views.resources, name="resources"),
    path("about/", views.about, name="about"),
    path("assistant/", views.assistant, name="assistant"),
]
