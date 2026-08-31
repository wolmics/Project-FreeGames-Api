"""File to read the config out of files."""

from pathlib import Path
from argparse import ArgumentParser, Namespace
from configparser import ConfigParser, SectionProxy
from dataclasses import dataclass

CONFIG_PATH = Path("config.ini")

@dataclass
class GeneralSettings:
    enabled: bool
    error_tries: int
    public_games: bool
    public_info: bool
    api_status_message: str


@dataclass
class DestinationSettings:
    output_folder: Path
    public_output_folder: Path
    cache_folder: Path


@dataclass
class NtfySettings:
    url: str
    token: str


@dataclass
class StatisticsSettings:
    update_statistics: bool
    public_statistics: bool


class ConfigError(Exception):
    """Raised when required config sections/keys are missing or invalid."""


class Config:
    @staticmethod
    def read_config() -> ConfigParser:
        config = ConfigParser()
        read_files = config.read(CONFIG_PATH)
        if not read_files:
            raise ConfigError(
                f"Config file not found at '{CONFIG_PATH}'. "
                f"Create it or check that it sits next to config.py."
            )
        return config

    @staticmethod
    def _section(config: ConfigParser, name: str) -> SectionProxy:
        """Return a section, or raise a clear error if it's missing."""
        if not config.has_section(name):
            raise ConfigError(
                f"Missing required section '[{name}]' in '{CONFIG_PATH}'."
            )
        return config[name]

    @staticmethod
    def _require(section, key: str, section_name: str) -> str:
        """Get a required key from a section, or raise a clear error."""
        if key not in section:
            raise ConfigError(
                f"Missing required key '{key}' in section '[{section_name}]' "
                f"of '{CONFIG_PATH}'."
            )
        return section[key]

    @staticmethod
    def get_destinations() -> DestinationSettings:
        config = Config.read_config()
        section = Config._section(config, "destinations")
        return DestinationSettings(
            output_folder=Path(Config._require(section, "output_folder", "destinations")),
            public_output_folder=Path(
                Config._require(section, "public_output_folder", "destinations")
            ),
            cache_folder=Path(Config._require(section, "cache_folder", "destinations")),
        )

    @staticmethod
    def get_ntfy() -> NtfySettings:
        # Ntfy is treated as optional: if the section is missing entirely,
        # fall back to empty values instead of crashing.
        config = Config.read_config()
        if not config.has_section("ntfy"):
            return NtfySettings(url="", token="")

        section = config["ntfy"]
        return NtfySettings(
            url=section.get("url", ""),
            token=section.get("token", ""),
        )

    @staticmethod
    def get_statistics() -> StatisticsSettings:
        config = Config.read_config()
        section = Config._section(config, "statistics")
        return StatisticsSettings(
            update_statistics=section.getboolean("update_statistics", fallback=False),
            public_statistics=section.getboolean("public_statistics", fallback=False),
        )

    @staticmethod
    def get_general_settings() -> GeneralSettings:
        config = Config.read_config()
        section = Config._section(config, "general")
        try:
            error_tries = int(Config._require(section, "error_tries", "general"))
        except ValueError as exc:
            raise ConfigError(
                f"Key 'error_tries' in section '[general]' must be an integer."
            ) from exc

        return GeneralSettings(
            enabled=section.getboolean("enabled", fallback=False),
            error_tries=error_tries,
            public_games=section.getboolean("public_games", fallback=False),
            public_info=section.getboolean("public_info", fallback=False),
            api_status_message=Config._require(
                section, "api_status_message", "general"
            ),
        )

    @staticmethod
    def get_arguments() -> Namespace:
        parser = ArgumentParser(
            description="Scan free games on multiple sites and saves them to a output folder."
        )

        parser.add_argument(
            "--set-message",
            help="Sets the message to be displayed to the user.",
        )

        return parser.parse_args()
