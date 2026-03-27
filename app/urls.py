from django.urls import path

from . import views

app_name = "app"

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("<int:pk>/", views.DetailView.as_view(), name="detail"),
    path("<int:pk>/results/", views.ResultsView.as_view(), name="results"),
    path("<int:question_id>/vote/", views.vote, name="vote"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("dashboard/polls/create/", views.question_create, name="question_create"),
    path("dashboard/polls/<int:pk>/update/", views.question_update, name="question_update"),
    path("dashboard/polls/<int:pk>/toggle-status/", views.question_toggle_status, name="question_toggle_status"),
    path("dashboard/polls/<int:pk>/delete/", views.question_delete, name="question_delete"),
    path(
        "dashboard/polls/<int:question_pk>/choices/create/",
        views.choice_create,
        name="choice_create",
    ),
    path("dashboard/choices/<int:pk>/update/", views.choice_update, name="choice_update"),
    path("dashboard/choices/<int:pk>/delete/", views.choice_delete, name="choice_delete"),
]
