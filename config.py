"""File to read the config out of files."""

from pathlib import Path
from argparse import ArgumentParser, Namespace
from configparser import ConfigParser
from dataclasses import dataclass


@dataclass
class GeneralSettings:
    enabled: bool
    error_tries: int
    api_message: str

@dataclass
class DestinationSettings:
    output_folder: Path
    public_output_folder: Path

@dataclass
class NtfySettings:
    url: str
    token: str

@dataclass
class StatisticsSettings:
    update_statistics: bool
    public_statistics: bool

class Config:
    @staticmethod
    def read_config() -> ConfigParser:
        config = ConfigParser()
        config.read("config.ini")

        return config

    @staticmethod
    def get_destinations():
        config = Config.read_config()
        return DestinationSettings(
            output_folder=Path(config["destinations"]["output_folder"]),
            public_output_folder=Path(config["destinations"]["public_output_folder"]),
        )

    @staticmethod
    def get_ntfy() -> NtfySettings:
        config = Config.read_config()
        return NtfySettings(
            url=config["ntfy"]["url"],
            token=config["ntfy"]["token"],
        )

    @staticmethod
    def get_statistics():
        config = Config.read_config()
        return StatisticsSettings(
            update_statistics=config["statistics"]["update_statistics"].lower()
            == "true",
            public_statistics=config["statistics"]["public_statistics"].lower()
            == "true",
        )

    @staticmethod
    def get_general_settings():
        config = Config.read_config()
        return GeneralSettings(
            enabled=config["general"]["enabled"].lower() == "true",
            error_tries=int(config["general"]["error_tries"]),
            api_message=config["general"]["api_message"],
        )

    @staticmethod
    def get_arguments() -> Namespace:
        parser = ArgumentParser(
            description="Scan free games on multiple sites and saves them to a output folder."
        )

        parser.add_argument(
            "--save-to-nginx",
            action="store_true",
            help="Saves the output file to nginx directory.",
        )

        return parser.parse_args()
