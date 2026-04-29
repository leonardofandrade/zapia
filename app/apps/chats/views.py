from django.http import HttpResponse
from rest_framework import viewsets
from rest_framework.decorators import action

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

    def get_queryset(self):
        queryset = super().get_queryset()
        chat_id = self.request.query_params.get("chat")
        if chat_id:
            queryset = queryset.filter(chat_id=chat_id)
        return queryset


class ChatMessageViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = (
        ChatMessage.objects.select_related("chat", "chat_import", "sender")
        .all()
        .order_by("sequence_index")
    )
    serializer_class = ChatMessageSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        chat_id = self.request.query_params.get("chat")
        if chat_id:
            queryset = queryset.filter(chat_id=chat_id)
        return queryset


class ChatAttachmentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ChatAttachment.objects.select_related("message").all().order_by("-created_at")
    serializer_class = ChatAttachmentSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        chat_id = self.request.query_params.get("chat")
        if chat_id:
            queryset = queryset.filter(message__chat_id=chat_id)
        return queryset

    @action(detail=True, methods=["get"], url_path="content")
    def content(self, request, pk=None):
        attachment = self.get_object()
        if not attachment.content_bytes:
            return HttpResponse(status=204)
        response = HttpResponse(
            attachment.content_bytes,
            content_type=attachment.mime_type or "application/octet-stream",
        )
        response["Content-Disposition"] = (
            f'inline; filename="{attachment.file_name or "attachment.bin"}"'
        )
        return response
