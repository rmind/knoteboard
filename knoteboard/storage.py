from functools import cache
from os import fsync, getenv, rename
from pathlib import Path
from tempfile import NamedTemporaryFile

from dateparser import DateDataParser

from knoteboard.models import AppDataModel
from knoteboard.utils import FileLock


class Storage:
    FILE_NAME = "knoteboard.json"

    base_path: Path
    state_file: Path
    locked: bool

    def __init__(self, path: str | None = None):
        path = path or getenv("KNOTEBOARD_PATH") or Path.home()
        self.base_path = Path(path) / ".knoteboard"

        # Ensure the directory.
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.state_file = self.base_path / self.FILE_NAME
        self.lock = FileLock(self.base_path)
        self.locked = self.lock.acquire()

        if not self.state_file.exists():
            self.state_file.touch(mode=0o600)
            self._initialize()

    def _initialize(self):
        self.save(AppDataModel.initialize())

    def title(self):
        return self.base_path.parent.absolute().name

    def load(self) -> AppDataModel:
        with open(self.state_file, "r") as fh:
            payload = fh.read()
            return AppDataModel.model_validate_json(payload)

    def save(self, data: AppDataModel):
        """
        Save the state/data into the file.
        Do it atomically.
        """

        assert self.locked, "the data directory must be 'locked'"

        # Create a temporary file with the state.
        temp_file = NamedTemporaryFile(
            prefix=f"{self.FILE_NAME}.", dir=self.base_path, delete=False
        )

        # Write, sync, rename.
        with open(temp_file.name, "w") as fh:
            payload = data.model_dump_json(indent=4)
            fh.write(payload)
            fsync(fh)
        rename(temp_file.name, self.state_file)

    def ensure_locked(self) -> bool:
        self.locked = self.locked or self.lock.acquire()
        return self.locked


@cache
def get_storage(path: str | None = None) -> Storage:
    return Storage(path)
