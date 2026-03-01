from datetime import datetime

try:
    from uuid import uuid7 as uuid
except ImportError:
    from uuid import uuid4 as uuid
from pydantic import BaseModel, model_validator


class ItemModel(BaseModel):
    title: str
    description: str | None = None
    date: datetime | None = None

    # Metadata:
    id: str = str(uuid())
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()
    completed_at: datetime | None = None


class ColumnModel(BaseModel):
    label: str
    items: list[ItemModel]
    terminal: bool = False

    @model_validator(mode="after")
    def check_label(self):
        if not self.label.strip():
            raise ValueError("the column label must not be empty")
        return self


class BoardModel(BaseModel):
    columns: list[ColumnModel]
    deleted: list[ItemModel] | None = None

    @model_validator(mode="after")
    def check_columns(self):
        if len(self.columns) == 0:
            raise ValueError("must have at least one column")
        return self


class AppDataModel(BaseModel):
    board: BoardModel

    @classmethod
    def initialize(cls):
        return AppDataModel(
            board=BoardModel(
                columns=[
                    ColumnModel(label="TO DO", items=[]),
                    ColumnModel(label="IN PROGRESS", items=[]),
                    ColumnModel(label="PENDING", items=[]),
                    ColumnModel(label="DONE", items=[], terminal=True),
                ]
            )
        )
