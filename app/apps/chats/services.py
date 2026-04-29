from __future__ import annotations

import hashlib
import mimetypes
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable
from zipfile import ZipFile

from django.db import transaction
from django.utils import timezone

from apps.subjects.models import Subject

from .models import ChatAttachment, ChatImport, ChatMessage, ChatParticipant, ChatThread

MESSAGE_LINE_RE = re.compile(
    r"^(?P<date>\d{2}/\d{2}/\d{4}) (?P<time>\d{2}:\d{2}) - (?P<body>.+)$"
)
AUTHOR_MESSAGE_RE = re.compile(r"^(?P<author>[^:]+): (?P<content>.*)$")
ATTACHMENT_PLACEHOLDER_RE = re.compile(r"^(?P<file_name>.+) \(arquivo anexado\)$")
PHONE_RE = re.compile(r"^\+?\d[\d\s\-()]{7,}$")
MEDIA_HIDDEN_TOKEN = "<Mídia oculta>"
MEDIA_PREFIXES = ("IMG-", "VID-", "AUD-", "PTT-", "STK-", "DOC-")


@dataclass(frozen=True)
class ParsedMessage:
    sequence_index: int
    raw_timestamp: str
    sent_at: datetime | None
    sender_name: str | None
    content: str
    message_type: str
    raw_line: str


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _normalized(value: str) -> str:
    return " ".join(value.strip().lower().split())


def _normalize_attachment_name(value: str) -> str:
    invisible_chars = ["\u200e", "\u200f", "\u202a", "\u202b", "\u202c", "\ufeff"]
    cleaned = value
    for char in invisible_chars:
        cleaned = cleaned.replace(char, "")
    return cleaned.strip()


def _is_media_file(file_name: str) -> bool:
    upper_name = Path(file_name).name.upper()
    if upper_name.endswith(".TXT") or upper_name.endswith(".VCF"):
        return False
    return upper_name.startswith(MEDIA_PREFIXES)


def _extract_message_date_key(raw_timestamp: str) -> str:
    # Converts "14/04/2025 09:11" -> "20250414"
    try:
        parsed = datetime.strptime(raw_timestamp, "%d/%m/%Y %H:%M")
        return parsed.strftime("%Y%m%d")
    except ValueError:
        return ""


def _resolve_attachment_from_media_hidden(
    *,
    content: str,
    raw_timestamp: str,
    archive_names: list[str],
    used_archive_names: set[str],
) -> str | None:
    first_line = content.splitlines()[0].strip() if content else ""
    if first_line != MEDIA_HIDDEN_TOKEN:
        return None

    date_key = _extract_message_date_key(raw_timestamp)
    candidates = [
        name
        for name in archive_names
        if name not in used_archive_names and _is_media_file(name)
    ]
    if date_key:
        dated_candidates = [name for name in candidates if date_key in Path(name).name]
        if dated_candidates:
            return dated_candidates[0]
    return candidates[0] if candidates else None


def _digits_only(value: str) -> str:
    return "".join(ch for ch in value if ch.isdigit())


def _extract_sender_identity(sender_name: str) -> tuple[str, str, str]:
    clean_name = sender_name.strip()
    if PHONE_RE.match(clean_name):
        phone_digits = _digits_only(clean_name)
        return clean_name, clean_name, phone_digits
    return clean_name, "", ""


def _build_subject_tax_id(*, display_name: str, phone_number: str, wa_id: str) -> str:
    if wa_id:
        return f"WAID:{wa_id}"
    if phone_number:
        return f"PHONE:{_digits_only(phone_number)}"
    sender_hash = _sha256(_normalized(display_name).encode("utf-8"))[:20]
    return f"CHAT:{sender_hash}"


def build_thread_fingerprint(title: str, is_group: bool) -> str:
    canonical = f"{_normalized(title)}|{'group' if is_group else 'direct'}"
    return _sha256(canonical.encode("utf-8"))


def build_message_fingerprint(
    *,
    sender_key: str,
    raw_timestamp: str,
    content: str,
    message_type: str,
) -> str:
    canonical = "|".join(
        [
            _normalized(sender_key),
            _normalized(raw_timestamp),
            _normalized(content),
            _normalized(message_type),
        ]
    )
    return _sha256(canonical.encode("utf-8"))


def build_attachment_fingerprint(
    *,
    file_name: str,
    content_hash: str,
    caption: str = "",
) -> str:
    canonical = "|".join(
        [_normalized(file_name), _normalized(content_hash), _normalized(caption)]
    )
    return _sha256(canonical.encode("utf-8"))


def _parse_sent_at(raw_timestamp: str) -> datetime | None:
    try:
        parsed = datetime.strptime(raw_timestamp, "%d/%m/%Y %H:%M")
        return timezone.make_aware(parsed, timezone.get_current_timezone())
    except ValueError:
        return None


def parse_whatsapp_export_lines(lines: Iterable[str]) -> list[ParsedMessage]:
    messages: list[ParsedMessage] = []
    current: ParsedMessage | None = None

    for raw in lines:
        line = raw.rstrip("\n")
        match = MESSAGE_LINE_RE.match(line)
        if not match:
            if current is None:
                continue
            current = ParsedMessage(
                sequence_index=current.sequence_index,
                raw_timestamp=current.raw_timestamp,
                sent_at=current.sent_at,
                sender_name=current.sender_name,
                content=f"{current.content}\n{line}".strip(),
                message_type=current.message_type,
                raw_line=current.raw_line,
            )
            messages[-1] = current
            continue

        body = match.group("body")
        raw_timestamp = f"{match.group('date')} {match.group('time')}"
        sent_at = _parse_sent_at(raw_timestamp)
        author_match = AUTHOR_MESSAGE_RE.match(body)

        sender_name: str | None = None
        content = body
        message_type = ChatMessage.MessageType.SYSTEM

        if author_match:
            sender_name = author_match.group("author").strip()
            content = author_match.group("content")
            if content == "Mensagem apagada":
                message_type = ChatMessage.MessageType.DELETED
            elif content == "<Mídia oculta>":
                message_type = ChatMessage.MessageType.MEDIA_PLACEHOLDER
            elif "<Mensagem editada>" in content:
                message_type = ChatMessage.MessageType.EDITED
            else:
                message_type = ChatMessage.MessageType.USER

        parsed = ParsedMessage(
            sequence_index=len(messages) + 1,
            raw_timestamp=raw_timestamp,
            sent_at=sent_at,
            sender_name=sender_name,
            content=content.strip(),
            message_type=message_type,
            raw_line=line,
        )
        messages.append(parsed)
        current = parsed

    return messages


def import_whatsapp_chat_zip(zip_path: str | Path) -> ChatImport:
    zip_file_path = Path(zip_path)
    with ZipFile(zip_file_path, "r") as archive:
        archive_names = archive.namelist()
        used_archive_names: set[str] = set()
        attachment_index: dict[str, str] = {}
        for archive_name in archive_names:
            normalized_name = _normalize_attachment_name(archive_name)
            attachment_index[normalized_name] = archive_name
            attachment_index[_normalize_attachment_name(Path(archive_name).name)] = archive_name

        text_name = next(
            (name for name in archive_names if name.lower().endswith(".txt")),
            None,
        )
        if text_name is None:
            raise ValueError("No WhatsApp chat text file found in zip archive.")

        text_bytes = archive.read(text_name)
        source_hash = _sha256(text_bytes)
        lines = text_bytes.decode("utf-8-sig", errors="replace").splitlines()
        parsed_messages = parse_whatsapp_export_lines(lines)
        chat_title = Path(text_name).stem.replace("Conversa do WhatsApp com ", "").strip()
        thread_fingerprint = build_thread_fingerprint(title=chat_title, is_group=True)

        with transaction.atomic():
            chat, _ = ChatThread.objects.get_or_create(
                thread_fingerprint=thread_fingerprint,
                defaults={
                    "title": chat_title or zip_file_path.stem,
                    "is_group": True,
                    "source_export_name": text_name,
                },
            )

            chat_import, _ = ChatImport.objects.get_or_create(
                chat=chat,
                source_hash=source_hash,
                defaults={"source_file_name": text_name},
            )

            participants_cache: dict[str, ChatParticipant] = {}

            for parsed in parsed_messages:
                sender = None
                sender_key = "system"
                if parsed.sender_name:
                    display_name, phone_number, wa_id = _extract_sender_identity(
                        parsed.sender_name
                    )
                    sender_key = _normalized(f"{display_name}|{phone_number}|{wa_id}")
                    sender = participants_cache.get(sender_key)
                    if sender is None:
                        subject_tax_id = _build_subject_tax_id(
                            display_name=display_name,
                            phone_number=phone_number,
                            wa_id=wa_id,
                        )
                        subject_defaults = {"full_name": display_name}
                        if display_name != phone_number and phone_number:
                            subject_defaults["alias"] = phone_number
                        subject, _ = Subject.objects.get_or_create(
                            tax_id=subject_tax_id,
                            defaults=subject_defaults,
                        )
                        sender, _ = ChatParticipant.objects.get_or_create(
                            chat=chat,
                            display_name=display_name,
                            phone_number=phone_number,
                            defaults={
                                "wa_id": wa_id,
                                "subject": subject,
                            },
                        )
                        if sender.subject_id is None:
                            sender.subject = subject
                            sender.wa_id = sender.wa_id or wa_id
                            sender.save(update_fields=["subject", "wa_id"])
                        participants_cache[sender_key] = sender

                message_fingerprint = build_message_fingerprint(
                    sender_key=sender_key,
                    raw_timestamp=parsed.raw_timestamp,
                    content=parsed.content,
                    message_type=parsed.message_type,
                )

                message, created = ChatMessage.objects.get_or_create(
                    chat=chat,
                    message_fingerprint=message_fingerprint,
                    defaults={
                        "chat_import": chat_import,
                        "sender": sender,
                        "sequence_index": parsed.sequence_index,
                        "message_type": parsed.message_type,
                        "sent_at": parsed.sent_at,
                        "raw_timestamp": parsed.raw_timestamp,
                        "content": parsed.content,
                        "raw_line": parsed.raw_line,
                        "is_edited": parsed.message_type
                        == ChatMessage.MessageType.EDITED,
                    },
                )

                attachment_match = ATTACHMENT_PLACEHOLDER_RE.match(parsed.content)
                archive_attachment_name: str | None = None
                attachment_name = ""
                caption = ""

                if attachment_match:
                    attachment_name = _normalize_attachment_name(
                        attachment_match.group("file_name")
                    )
                    archive_attachment_name = attachment_index.get(attachment_name)
                else:
                    archive_attachment_name = _resolve_attachment_from_media_hidden(
                        content=parsed.content,
                        raw_timestamp=parsed.raw_timestamp,
                        archive_names=archive_names,
                        used_archive_names=used_archive_names,
                    )
                    if archive_attachment_name:
                        attachment_name = Path(archive_attachment_name).name
                        lines = parsed.content.splitlines()
                        caption = "\n".join(lines[1:]).strip() if len(lines) > 1 else ""

                if archive_attachment_name is None:
                    continue

                content_bytes = archive.read(archive_attachment_name)
                content_hash = _sha256(content_bytes)
                attachment_fingerprint = build_attachment_fingerprint(
                    file_name=attachment_name,
                    content_hash=content_hash,
                    caption=caption,
                )
                mime_type, _ = mimetypes.guess_type(archive_attachment_name)
                suffix = Path(archive_attachment_name).suffix.lstrip(".").lower()

                ChatAttachment.objects.get_or_create(
                    message=message,
                    attachment_fingerprint=attachment_fingerprint,
                    defaults={
                        "file_name": Path(archive_attachment_name).name,
                        "mime_type": mime_type or "",
                        "file_extension": suffix,
                        "content_bytes": content_bytes,
                        "content_size": len(content_bytes),
                        "sha256": content_hash,
                        "caption": caption,
                    },
                )
                used_archive_names.add(archive_attachment_name)

    return chat_import
