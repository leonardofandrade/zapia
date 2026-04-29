from django.db import models


class ChatThread(models.Model):
    """Represents a WhatsApp conversation thread (group or direct chat)."""

    title = models.CharField(max_length=255)
    is_group = models.BooleanField(default=True)
    thread_fingerprint = models.CharField(max_length=64, unique=True)
    source_export_name = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "chats_thread"

    def __str__(self) -> str:
        return self.title


class ChatImport(models.Model):
    """Tracks one import execution/source file for a conversation export."""

    chat = models.ForeignKey(
        ChatThread,
        on_delete=models.CASCADE,
        related_name="imports",
    )
    source_file_name = models.CharField(max_length=255)
    source_hash = models.CharField(max_length=64, blank=True)
    imported_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "chats_import"
        constraints = [
            models.UniqueConstraint(
                fields=["chat", "source_hash"],
                condition=~models.Q(source_hash=""),
                name="uq_chats_import_chat_source_hash",
            )
        ]

    def __str__(self) -> str:
        return f"{self.source_file_name} ({self.imported_at:%Y-%m-%d %H:%M:%S})"


class ChatParticipant(models.Model):
    """Represents a participant identified during chat import parsing."""

    chat = models.ForeignKey(
        ChatThread,
        on_delete=models.CASCADE,
        related_name="participants",
    )
    display_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=30, blank=True)
    wa_id = models.CharField(max_length=30, blank=True)
    is_self = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "chats_participant"
        constraints = [
            models.UniqueConstraint(
                fields=["chat", "phone_number", "display_name"],
                name="uq_chats_participant_identity_per_chat",
            )
        ]

    def __str__(self) -> str:
        return f"{self.display_name} ({self.phone_number or 'unknown'})"


class ChatMessage(models.Model):
    """Stores parsed message/event rows from a WhatsApp exported text file."""

    class MessageType(models.TextChoices):
        USER = "USER", "User Message"
        SYSTEM = "SYSTEM", "System Event"
        MEDIA_PLACEHOLDER = "MEDIA_PLACEHOLDER", "Media Placeholder"
        DELETED = "DELETED", "Deleted Message"
        EDITED = "EDITED", "Edited Message"
        UNKNOWN = "UNKNOWN", "Unknown"

    chat = models.ForeignKey(
        ChatThread,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    chat_import = models.ForeignKey(
        ChatImport,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    sender = models.ForeignKey(
        ChatParticipant,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="messages",
    )
    sequence_index = models.PositiveIntegerField()
    message_type = models.CharField(
        max_length=20,
        choices=MessageType.choices,
        default=MessageType.USER,
    )
    sent_at = models.DateTimeField(null=True, blank=True)
    raw_timestamp = models.CharField(max_length=30, blank=True)
    content = models.TextField(blank=True)
    raw_line = models.TextField(blank=True)
    message_fingerprint = models.CharField(max_length=64)
    is_edited = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "chats_message"
        constraints = [
            models.UniqueConstraint(
                fields=["chat_import", "sequence_index"],
                name="uq_chats_message_sequence_per_import",
            ),
            models.UniqueConstraint(
                fields=["chat", "message_fingerprint"],
                name="uq_chats_message_fingerprint_per_chat",
            ),
        ]
        ordering = ["sequence_index"]

    def __str__(self) -> str:
        sender_name = self.sender.display_name if self.sender else "System"
        return f"{sender_name}: {self.content[:40] or self.message_type}"


class ChatAttachment(models.Model):
    """Persists attachment metadata and binary content directly in the database."""

    message = models.ForeignKey(
        ChatMessage,
        on_delete=models.CASCADE,
        related_name="attachments",
    )
    file_name = models.CharField(max_length=255)
    mime_type = models.CharField(max_length=120, blank=True)
    file_extension = models.CharField(max_length=20, blank=True)
    content_bytes = models.BinaryField(null=True, blank=True)
    content_size = models.PositiveBigIntegerField(default=0)
    sha256 = models.CharField(max_length=64, blank=True)
    attachment_fingerprint = models.CharField(max_length=64, blank=True)
    caption = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "chats_attachment"
        constraints = [
            models.UniqueConstraint(
                fields=["message", "sha256"],
                condition=~models.Q(sha256=""),
                name="uq_chats_attachment_sha256_per_message",
            ),
            models.UniqueConstraint(
                fields=["message", "attachment_fingerprint"],
                condition=~models.Q(attachment_fingerprint=""),
                name="uq_chats_attachment_fp_per_message",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.file_name} ({self.content_size} bytes)"
