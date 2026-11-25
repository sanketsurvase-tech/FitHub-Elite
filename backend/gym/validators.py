from pathlib import Path

from django.core.exceptions import ValidationError


def validate_member_document(file):
    if file.size > 5 * 1024 * 1024:
        raise ValidationError("Documents must be 5 MB or smaller.")
    extension = Path(file.name).suffix.lower()
    file.seek(0)
    header = file.read(8)
    file.seek(0)
    valid = (
        extension == ".pdf" and header.startswith(b"%PDF-")
    ) or (
        extension in {".jpg", ".jpeg"} and header.startswith(b"\xff\xd8\xff")
    ) or (
        extension == ".png" and header.startswith(b"\x89PNG\r\n\x1a\n")
    )
    if not valid:
        raise ValidationError("Upload a valid PDF, JPEG, or PNG document.")
