from rest_framework import viewsets

from .models import ChatAttachment, ChatImport, ChatMessage, ChatParticipant, ChatThread
from .serializers import (
    ChatAttachmentSerializer,
    ChatImportSerializer,
    ChatMessageSerializer,
    ChatParticipantSerializer,
    ChatThreadSerializer,
)


class ChatThreadViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ChatThread.objects.all().order_by("-created_at")
    serializer_class = ChatThreadSerializer


class ChatImportViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ChatImport.objects.select_related("chat").all().order_by("-imported_at")
    serializer_class = ChatImportSerializer


class ChatParticipantViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ChatParticipant.objects.select_related("chat").all().order_by("-created_at")
    serializer_class = ChatParticipantSerializer


class ChatMessageViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = (
        ChatMessage.objects.select_related("chat", "chat_import", "sender")
        .all()
        .order_by("sequence_index")
    )
    serializer_class = ChatMessageSerializer


class ChatAttachmentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ChatAttachment.objects.select_related("message").all().order_by("-created_at")
    serializer_class = ChatAttachmentSerializer
