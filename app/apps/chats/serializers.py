from rest_framework import serializers

from .models import ChatAttachment, ChatImport, ChatMessage, ChatParticipant, ChatThread


class ChatThreadSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatThread
        fields = [
            "id",
            "title",
            "is_group",
            "thread_fingerprint",
            "source_export_name",
            "created_at",
        ]


class ChatImportSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatImport
        fields = ["id", "chat", "source_file_name", "source_hash", "imported_at"]


class ChatParticipantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatParticipant
        fields = [
            "id",
            "chat",
            "display_name",
            "phone_number",
            "wa_id",
            "is_self",
            "created_at",
        ]


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = [
            "id",
            "chat",
            "chat_import",
            "sender",
            "sequence_index",
            "message_type",
            "sent_at",
            "raw_timestamp",
            "content",
            "raw_line",
            "message_fingerprint",
            "is_edited",
            "created_at",
        ]


class ChatAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatAttachment
        fields = [
            "id",
            "message",
            "file_name",
            "mime_type",
            "file_extension",
            "content_size",
            "sha256",
            "attachment_fingerprint",
            "caption",
            "created_at",
        ]
