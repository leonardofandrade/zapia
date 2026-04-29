from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ChatAttachmentViewSet,
    ChatImportViewSet,
    ChatMessageViewSet,
    ChatParticipantViewSet,
    ChatThreadViewSet,
)

router = DefaultRouter()
router.register("threads", ChatThreadViewSet, basename="chat-thread")
router.register("imports", ChatImportViewSet, basename="chat-import")
router.register("participants", ChatParticipantViewSet, basename="chat-participant")
router.register("messages", ChatMessageViewSet, basename="chat-message")
router.register("attachments", ChatAttachmentViewSet, basename="chat-attachment")

urlpatterns = [
    path("", include(router.urls)),
]
