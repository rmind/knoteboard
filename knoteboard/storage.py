from functools import cache
from os import fsync, getenv, rename
from pathlib import Path
from tempfile import NamedTemporaryFile

from dateparser import DateDataParser

from knoteboard.models import AppDataModel


class Storage:
    FILE_NAME = "knoteboard.json"

    base_path: Path

    def __init__(self, path: str | None = None):
        path = path or getenv("KNOTEBOARD_PATH") or Path.home()
        self.base_path = Path(path) / ".knoteboard"

    def title(self):
        return self.base_path.parent.absolute().name

    def _initialize(self):
        self.save(AppDataModel.initialize())

    def load(self) -> AppDataModel:
        state_dir = Path(self.base_path)
        state_dir.mkdir(parents=True, exist_ok=True)

        state_file = state_dir / self.FILE_NAME
        if not state_file.exists():
            state_file.touch(mode=0o600)
            self._initialize()

        with open(state_file, "r") as fh:
            payload = fh.read()
            return AppDataModel.model_validate_json(payload)

    def save(self, data: AppDataModel):
        """
        Save the state/data into the file.
        Do it atomically.
        """

        # Ensure the directory.
        state_dir = Path(self.base_path)
        state_dir.mkdir(parents=True, exist_ok=True)
        state_file = state_dir / self.FILE_NAME

        # Create a temporary file with the state.
        temp_file = NamedTemporaryFile(
            prefix=f"{self.FILE_NAME}.", dir=state_dir, delete=False
        )

        # Write, sync, rename.
        with open(temp_file.name, "w") as fh:
            payload = data.model_dump_json(indent=4)
            fh.write(payload)
            fsync(fh)
        rename(temp_file.name, state_file)


@cache
def get_storage(path: str | None = None) -> Storage:
    return Storage(path)
