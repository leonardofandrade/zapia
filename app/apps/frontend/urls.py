from django.urls import path

from .views import ChatDetailView, ChatsListView, DashboardView, SubjectsListView

urlpatterns = [
    path("", DashboardView.as_view(), name="dashboard"),
    path("subjects/", SubjectsListView.as_view(), name="subjects-list-page"),
    path("chats/", ChatsListView.as_view(), name="chats-list-page"),
    path("chats/<int:chat_id>/", ChatDetailView.as_view(), name="chat-detail-page"),
]
