"""
Utilidades para manejar imágenes que llegan a posts/comentarios.

Estrategia: la imagen viaja embebida en el documento de Mongo como Base64
(campos `image_base64` y `image_mime`). Esto evita servir archivos estáticos
y mantiene un único lugar de verdad. El frontend reconstruye el data URL con
`data:{mime};base64,{image_base64}` para mostrarlo en un <img>.

Se aceptan dos formatos de entrada en routes:
  1. JSON con `image_base64` (con o sin prefijo `data:...;base64,`).
  2. multipart/form-data con un archivo bajo el campo `image`.
"""
import base64
import binascii
from typing import Tuple

from werkzeug.datastructures import FileStorage

from .schemas import ALLOWED_IMAGE_MIMES, MAX_IMAGE_BYTES


class ImageError(ValueError):
    """Error semántico al procesar la imagen (mime/tamaño/encoding)."""


def _strip_data_url_prefix(b64: str) -> Tuple[str, str | None]:
    """
    Si el string viene con prefijo `data:image/png;base64,XXXX`, lo separa.
    Devuelve (base64_payload, mime_inferido_o_None).
    """
    if b64.startswith("data:"):
        try:
            header, payload = b64.split(",", 1)
            # header == "data:image/png;base64"
            mime_part = header[5:].split(";")[0].strip().lower() or None
            return payload, mime_part
        except ValueError:
            return b64, None
    return b64, None


def normalize_base64_image(raw_b64: str, mime: str | None) -> Tuple[str, str]:
    """
    Valida y normaliza un Base64 entrante. Devuelve (b64_limpio, mime).

    Lanza ImageError si:
      - el mime no está en la lista blanca,
      - el Base64 no es decodificable,
      - el contenido decodificado supera MAX_IMAGE_BYTES.
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

    # Saneamos posibles saltos de línea/espacios que ensucian un Base64.
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
