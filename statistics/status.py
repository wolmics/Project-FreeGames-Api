"""A class to manage the status of FreeGames Api"""

from os import makedirs
from json import loads, dumps, JSONDecodeError
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime

from config import Config

@dataclass
class Status:
    last_scan: str
    error: bool
    message: str

class StatusManager:
    """Manages the status of FreeGames Api"""
    def __init__(self):
        makedirs(Config.get_destinations().output_folder, exist_ok=True)
        self.public: bool = Config.get_general_settings().public_info
        self.output: Path = Config.get_destinations().output_folder / 'status.json'

        if self.public:
            makedirs(Config.get_destinations().public_output_folder, exist_ok=True)
            self.public_output: Path = Config.get_destinations().public_output_folder / 'status.json'

        self.status_message_path: Path = Config.get_destinations().cache_folder / 'status_message.txt'

    """ Public functions """

    def set_message(self, message: str) -> None:
        """Sets a current status message"""
        self._add('message', message)
        self._write_message_backup(message)

    def after_run(self, success: bool) -> None:
        """Sets the status after a run"""
        self._add('last_scan', datetime.now().isoformat())
        self._add('successfully', success)

    """ Private functions """

    def _load(self) -> Status:
        """Loads the status file, falling back to the message backup if the json is missing/corrupt"""
        file = Path(self.output)
        self._file_check(file)

        try:
            data = loads(file.read_text(encoding='utf-8'))
        except JSONDecodeError:
            data = asdict(Status(
                last_scan='',
                error=False,
                message=self._read_message_backup(),
            ))

        return self._dict_to_status(data)

    def _add(self, key, value) -> None:
        """Adds a key and value to the current status"""
        current_status = asdict(self._load())
        current_status[key] = value

        self._dump(self._dict_to_status(current_status))

    def _dump(self, status: Status) -> None:
        """Dumps a Status object to a file"""
        self.output.write_text(dumps(asdict(status), indent=4))
        self._sync_status()

    def _sync_status(self) -> None:
        """Synchronizes local and public status"""
        if self.public:
            status = self._load()
            self.public_output.write_text(dumps(asdict(status), indent=4))

    def _write_message_backup(self, message: str) -> None:
        """Writes the current status message to a plain-text backup file"""
        self.status_message_path.write_text(message, encoding='utf-8')

    def _read_message_backup(self) -> str:
        """Reads the backed-up status message, or '' if none exists yet"""
        if self.status_message_path.exists():
            return self.status_message_path.read_text(encoding='utf-8')
        return ''

    """ Static private functions """

    @staticmethod
    def _dict_to_status(status_dict: dict) -> Status:
        """Converts a dict to a Status object"""
        return Status(
            status_dict['last_scan'],
            status_dict['error'],
            status_dict['message'],
        )

    def _file_check(self, path: Path) -> None:
        """Checks if the file exists; recreates it using the message backup if missing"""
        if not path.exists():
            default_status = Status(
                last_scan='',
                error=False,
                message=self._read_message_backup(),
            )
            path.write_text(dumps(asdict(default_status), indent=4), encoding='utf-8')