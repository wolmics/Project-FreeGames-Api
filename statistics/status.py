"""A class to manage the status of FreeGames Api"""

from os import makedirs
from json import loads, dumps
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime

from config import Config

@dataclass
class Status:
    last_scan: str
    error: bool
    message: str
    id: int

class StatusManager:
    """Manages the status of FreeGames Api"""
    def __init__(self):
        makedirs(Config.get_destinations().output_folder, exist_ok=True)
        self.public = Config.get_general_settings().public_info
        self.output = Config.get_destinations().output_folder / 'status.json'
        if self.public:
            makedirs(Config.get_destinations().public_output_folder, exist_ok=True)
            self.public_output = Config.get_destinations().public_output_folder / 'status.json'

    def load(self) -> Status:
        """Loads the """
        file = Path(self.output)
        self.file_check(file)

        data = loads(file.read_text(encoding='utf-8'))

        return self.dict_to_status(data)

    def file_check(self, path: Path):
        if not path.exists():
            default_status = Status(
                last_scan='',
                error=False,
                message='',
                id=0,
            )
            path.write_text(dumps(asdict(default_status), indent=4), encoding='utf-8')

    def add(self, key, value) -> None:
        """Adds a key and value to the current status"""
        current_status = asdict(self.load())
        current_status[key] = value

        self.dump(self.dict_to_status(current_status))

    def dict_to_status(self, status_dict: dict) -> Status:
        """Converts a dict to a Status object"""
        return Status(
            status_dict['last_scan'],
            status_dict['error'],
            status_dict['message'],
            status_dict['id'],
        )

    def dump(self, status: Status) -> None:
        """Dumps a Status object to a file"""
        self.output.write_text(dumps(asdict(status), indent=4))
        self.sync_status()

    def sync_status(self) -> None:
        """Synchronizes local and public status"""
        if self.public:
            status = self.load()
            self.public_output.write_text(dumps(asdict(status), indent=4))

    def new_message(self, message: str) -> None:
        """Adds a new message to the current status"""
        current_status = self.load()

        self.add('message', message)
        self.add('id', current_status.id + 1)

    def after_run(self, success: bool):
        self.add('last_scan', datetime.now().isoformat())
        self.add('error', not success)
