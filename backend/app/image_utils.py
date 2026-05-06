"""
Utilidades compartidas para manejar imágenes embebidas en Base64.

Estrategia: la imagen viaja en el documento de Mongo como Base64
(campos `*_base64` y `*_mime`). El frontend reconstruye el data URL con
`data:{mime};base64,{b64}` para mostrarlo en un <img>.

Se aceptan dos formatos de entrada:
  1. JSON con `*_base64` (con o sin prefijo `data:...;base64,`).
  2. multipart/form-data con un archivo bajo el campo correspondiente.
"""
import base64
import binascii
from typing import Tuple

from werkzeug.datastructures import FileStorage

ALLOWED_IMAGE_MIMES: frozenset[str] = frozenset({
    "image/png", "image/jpeg", "image/jpg", "image/gif", "image/webp"
})
MAX_IMAGE_BYTES: int = 5 * 1024 * 1024


class ImageError(ValueError):
    """Error semántico al procesar la imagen (mime/tamaño/encoding)."""


def _strip_data_url_prefix(b64: str) -> Tuple[str, str | None]:
    if b64.startswith("data:"):
        try:
            header, payload = b64.split(",", 1)
            mime_part = header[5:].split(";")[0].strip().lower() or None
            return payload, mime_part
        except ValueError:
            return b64, None
    return b64, None


def normalize_base64_image(raw_b64: str, mime: str | None) -> Tuple[str, str]:
    """
    Valida y normaliza un Base64 entrante. Devuelve (b64_limpio, mime).

    Lanza ImageError si el mime no está en lista blanca, el Base64 es
    inválido, o el contenido supera MAX_IMAGE_BYTES.
    """
    if not isinstance(raw_b64, str) or not raw_b64.strip():
        raise ImageError("La imagen Base64 está vacía")

    payload, inferred_mime = _strip_data_url_prefix(raw_b64.strip())
    final_mime = (mime or inferred_mime or "").strip().lower()

    if not final_mime:
        raise ImageError("Falta el tipo de imagen (image_mime)")
    if final_mime not in ALLOWED_IMAGE_MIMES:
        raise ImageError(
            f"Tipo de imagen no permitido. Permitidos: {sorted(ALLOWED_IMAGE_MIMES)}"
        )

    cleaned_payload = "".join(payload.split())

    try:
        decoded = base64.b64decode(cleaned_payload, validate=True)
    except (binascii.Error, ValueError) as ex:
        raise ImageError(f"Base64 inválido: {ex}") from ex

    if len(decoded) == 0:
        raise ImageError("La imagen está vacía tras decodificar")
    if len(decoded) > MAX_IMAGE_BYTES:
        raise ImageError(
            f"La imagen supera el tamaño máximo permitido "
            f"({MAX_IMAGE_BYTES // (1024 * 1024)} MB)"
        )

    return cleaned_payload, final_mime


def file_storage_to_base64(file: FileStorage) -> Tuple[str, str]:
    """
    Convierte un archivo subido (multipart/form-data) a (b64, mime).
    Aplica las mismas validaciones que `normalize_base64_image`.
    """
    if file is None or not getattr(file, "filename", ""):
        raise ImageError("No se recibió archivo de imagen")

    raw = file.read()
    if not raw:
        raise ImageError("El archivo de imagen está vacío")
    if len(raw) > MAX_IMAGE_BYTES:
        raise ImageError(
            f"La imagen supera el tamaño máximo permitido "
            f"({MAX_IMAGE_BYTES // (1024 * 1024)} MB)"
        )

    mime = (file.mimetype or "").strip().lower()
    if mime not in ALLOWED_IMAGE_MIMES:
        raise ImageError(
            f"Tipo de imagen no permitido. Permitidos: {sorted(ALLOWED_IMAGE_MIMES)}"
        )

    encoded = base64.b64encode(raw).decode("ascii")
    return encoded, mime
