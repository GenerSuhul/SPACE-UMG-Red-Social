from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Literal

# ---------------------------------------------------------------------------
# Tipos de reacciones permitidas (Posts y Comments comparten el mismo set).
# ---------------------------------------------------------------------------
ReactionType = Literal["like", "love", "haha", "wow", "sad", "angry"]
TargetType   = Literal["post", "comment"]


# ---------------------------------------------------------------------------
# POSTS
# ---------------------------------------------------------------------------
class PostCreateSchema(BaseModel):
    """
    Schema para crear una publicación.
    El `author_id` no se envía: se extrae del JWT en la capa de service.
    """
    model_config = ConfigDict(extra="forbid")

    content:    str         = Field(..., min_length=1, max_length=5000)
    media_urls: list[str]   = Field(default_factory=list)

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("El contenido no puede estar vacío")
        return cleaned

    @field_validator("media_urls")
    @classmethod
    def validate_media_urls(cls, value: list[str]) -> list[str]:
        if value is None:
            return []
        if len(value) > 10:
            raise ValueError("Máximo 10 URLs de media por post")
        for url in value:
            if not isinstance(url, str) or not url.strip():
                raise ValueError("Las URLs de media deben ser strings no vacíos")
        return [u.strip() for u in value]


class PostResponseSchema(BaseModel):
    """Schema canónico para serializar un post en respuestas."""
    id:               str
    author_id:        str
    content:          str
    media_urls:       list[str]
    created_at:       str
    updated_at:       str | None = None
    reactions_count:  dict[str, int]
    comments_count:   int


# ---------------------------------------------------------------------------
# COMMENTS
# ---------------------------------------------------------------------------
class CommentCreateSchema(BaseModel):
    """
    Schema para crear un comentario en un post.
    `post_id` viene de la URL, `author_id` del JWT — ambos se inyectan en service.
    """
    model_config = ConfigDict(extra="forbid")

    content:           str       = Field(..., min_length=1, max_length=2000)
    parent_comment_id: str | None = None

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("El comentario no puede estar vacío")
        return cleaned


class CommentResponseSchema(BaseModel):
    """Schema canónico para serializar un comentario en respuestas."""
    id:                str
    post_id:           str
    author_id:         str
    content:           str
    parent_comment_id: str | None = None
    created_at:        str
    reactions_count:   dict[str, int]


# ---------------------------------------------------------------------------
# REACTIONS
# ---------------------------------------------------------------------------
class ReactionCreateSchema(BaseModel):
    """
    Schema para reaccionar a un post o comentario.
    `target_id`, `target_type` y `user_id` se inyectan en service.
    """
    model_config = ConfigDict(extra="forbid")

    reaction_type: ReactionType


class ReactionResponseSchema(BaseModel):
    """Schema canónico para serializar una reacción en respuestas."""
    id:            str
    user_id:       str
    target_id:     str
    target_type:   TargetType
    reaction_type: ReactionType
    created_at:    str


# ---------------------------------------------------------------------------
# Helpers de inicialización
# ---------------------------------------------------------------------------
def empty_reactions_count() -> dict[str, int]:
    """Retorna un dict con todos los tipos de reacción inicializados a 0."""
    return {"like": 0, "love": 0, "haha": 0, "wow": 0, "sad": 0, "angry": 0}
