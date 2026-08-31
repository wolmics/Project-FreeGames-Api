#!/usr/bin/env bash

"""Script to scan for free games"""

from json import dumps
from time import sleep
import traceback

from dataclasses import asdict

from logger import setup_logger
from config import Config, DestinationSettings

from api.steam import scan as steam_scan
from api.gog import scan as gog_scan
from api.epicgames.epicgames import scan as epicgames_scan

from statistics.statistics import Statistics
from statistics.timer import Timer
from statistics.status import StatusManager
from structures import Game

logger = setup_logger(__name__)


class Runtime:
    def __init__(self, stats_obj: Statistics, timer_obj: Timer, status_manager_obj: StatusManager) -> None:
        self.statistics = stats_obj
        self.timer = timer_obj
        self.status_manager = status_manager_obj

        self.scans = {"epicgames": epicgames_scan, "steam": steam_scan, "gog": gog_scan}
        self.settings = Config.get_general_settings()

    def run(self) -> None:

        logger.info("Now scanning for free games...")

        for _ in range(0, self.settings.error_tries):
            try:
                free_games, success = self._scan()

                self.status_manager.after_run(success)
                self.statistics.update(free_games, success)
                if success:
                    self._save_games(free_games)
                    return

            except KeyboardInterrupt:
                logger.debug("Caught KeyboardInterrupt, exiting.")
                return
            except Exception as e:
                logger.error("There was an error with the api: %s", e)
                logger.error(traceback.format_exc())

            sleep(180)
        logger.critical(
            "There are multiple errors with the FreeGames api. Please fix instant!"
        )

    def _scan(self) -> tuple[list[Game], bool]:
        self.timer.start("total_duration")

        free_games = []
        for name, function in self.scans.items():
            self.timer.start(name)

            try:
                scanned_games = function()
                free_games.extend(scanned_games)
            except Exception as e:
                logger.error("There was an error with the api : %s", e)

            duration = self.timer.stop(name, log=True)
            self.statistics.dump(f"{name}_duration", duration)

        total_duration = self.timer.stop("total_duration", log=True)
        self.statistics.dump("total_duration", total_duration)
        return free_games, True

    @staticmethod
    def _save_games(free_games: list[Game]) -> None:
        """Saves the games either to nginx or output directory."""
        free_games_dict = [asdict(game) for game in free_games]

        private_path = Config.get_destinations().output_folder / "games.json"
        private_path.write_text(dumps(free_games_dict, indent=4))

        if Config.get_general_settings().public_games:
            public_path = Config.get_destinations().public_output_folder / "games.json"
            public_path.write_text(dumps(free_games_dict, indent=4))

    @staticmethod
    def create_directories() -> None:
        """Creates the necessary directories."""
        settings: DestinationSettings = Config.get_destinations()
        settings.output_folder.mkdir(parents=True, exist_ok=True)
        settings.public_output_folder.mkdir(parents=True, exist_ok=True)
        settings.cache_folder.mkdir(parents=True, exist_ok=True)

if __name__ == "__main__":
    Runtime.create_directories()
    arguments = Config.get_arguments()


    status_manager = StatusManager()

    if arguments.set_message:
        status_manager.set_message(arguments.set_message)
        logger.info("Successfully set the status message.")
        exit(0)


    general_settings = Config.get_general_settings()
    if general_settings.enabled:

        timer = Timer()
        statistics = Statistics()

        runtime = Runtime(statistics, timer, status_manager)
        runtime.run()

    else:
        logger.info("The FreeGames API has not been enabled.")

    exit(0)
