from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from apps.chats.services import import_whatsapp_chat_zip


class Command(BaseCommand):
    help = "Import a WhatsApp exported ZIP into chats models."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "zip_path",
            type=str,
            help="Absolute or relative path to WhatsApp export ZIP file.",
        )

    def handle(self, *args, **options) -> None:
        zip_path = Path(options["zip_path"]).expanduser()
        if not zip_path.exists() or not zip_path.is_file():
            raise CommandError(f"ZIP file not found: {zip_path}")
        if zip_path.suffix.lower() != ".zip":
            raise CommandError(f"Expected a .zip file, got: {zip_path.name}")

        try:
            chat_import = import_whatsapp_chat_zip(zip_path=zip_path)
        except Exception as exc:
            raise CommandError(f"Import failed: {exc}") from exc

        self.stdout.write(
            self.style.SUCCESS(
                "Import completed successfully: "
                f"chat_id={chat_import.chat_id}, import_id={chat_import.id}"
            )
        )
