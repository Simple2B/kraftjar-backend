import enum
from pydantic import BaseModel, ConfigDict


class FileType(enum.Enum):
    IMAGE = "image"
    VIDEO = "video"
    ATTACHMENT = "attachment"
    AVATAR = "avatar"
    UNKNOWN = "unknown"


class File(BaseModel):
    name: str = ""
    original_name: str = ""
    type: str = FileType.IMAGE.value
    url: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class FileIn(BaseModel):
    name: str
    file_base64: str
    type: str = FileType.IMAGE.value

    model_config = ConfigDict(
        from_attributes=True,
    )


class FileOut(File):
    uuid: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class DocumentOut(BaseModel):
    url: str
    title: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class Files(BaseModel):
    files: list[FileOut]

    model_config = ConfigDict(
        from_attributes=True,
    )
