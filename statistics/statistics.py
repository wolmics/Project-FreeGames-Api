"""Class to make statistics out of scanned free games"""

from json import dumps, loads

from structures import Game

from config import Config
from logger import setup_logger
from statistics import timer

logger = setup_logger(__name__)


class Statistics:
    """Class to make statistics for freegames api"""

    def __init__(self) -> None:
        """Sets up path"""
        self.stats = {}
        self.stats_dump = {}
        self.statistic_file = Config.get_destinations().output_folder / "statistics.json"
        self.timer = timer.Timer()

    def create_statistic_file(self) -> None:
        """Creates and writes the data structure to the file"""
        data_structure = {
            "total_scans": 0,
            "average_success": {"success": 0, "fails": 0},
            "average_money": {"total_money": 0, "maximum_price": 0},
            "average_money_store": [
                {"name": "steam", "total_money": 0, "maximum_price": 0},
                {"name": "epicgames", "total_money": 0, "maximum_price": 0},
                {"name": "gog", "total_money": 0, "maximum_price": 0},
            ],
            "average_scantime": {
                "total_scantime": 0,
                "maximum_scantime": 0,
                "minimum_scantime": 0,
            },
            "average_scantime_store": [
                {
                    "name": "steam",
                    "total_scantime": 0,
                    "maximum_scantime": 0,
                    "minimum_scantime": 0,
                },
                {
                    "name": "epicgames",
                    "total_scantime": 0,
                    "maximum_scantime": 0,
                    "minimum_scantime": 0,
                },
                {
                    "name": "gog",
                    "total_scantime": 0,
                    "maximum_scantime": 0,
                    "minimum_scantime": 0,
                },
            ],
            "all_games": [],
        }
        self.statistic_file.touch(exist_ok=True)
        self.statistic_file.write_text(dumps(data_structure, indent=4))

    def read_statistic_file(self) -> dict:
        """Check if file exists, else create one. Then read it."""
        if self.statistic_file.exists():
            self.create_statistic_file()

        data = loads(self.statistic_file.read_text(encoding="utf-8"))

        data["all_games"] = set(data["all_games"])
        return data

    def write(self) -> None:
        """Replaces set with list, and saves."""
        self.stats["all_games"] = list(self.stats["all_games"])

        self.statistic_file.write_text(dumps(self.stats, indent=4), encoding="utf-8")

        if Config.get_statistics().public_statistics:
            file_path = Config.get_destinations().public_output_folder / "statistics.json"
            file_path.write_text(
                dumps(self.stats, indent=4),
                encoding="utf-8"
            )

    def dump(self, key: str, value: float) -> None:
        """Dumps data into a dictionarry."""
        self.stats_dump.update({key: value})

    def is_game_new(self, game: Game) -> bool:
        """Checks if game is in the all_games list."""
        name = game.name
        shop = game.shop

        return f"{name}@{shop}" not in self.stats["all_games"]

    def update_scantime(self) -> None:
        """Updates the scantime statistics."""

        total_duration = self.stats_dump["total_duration"]
        avg_stats = self.stats["average_scantime"]

        avg_stats["total_scantime"] += total_duration
        avg_stats["maximum_scantime"] = max(
            avg_stats["maximum_scantime"], total_duration
        )
        avg_stats["minimum_scantime"] = min(
            avg_stats["minimum_scantime"], total_duration
        )

        for item in self.stats["average_scantime_store"]:
            name = item["name"]
            duration = self.stats_dump[f"{name}_duration"]

            item["total_scantime"] += duration
            item["maximum_scantime"] = max(item["maximum_scantime"], duration)
            item["minimum_scantime"] = min(item["minimum_scantime"], duration)

    def update_money(self, free_games: list[Game]) -> None:
        """Updates all the money items."""
        for game in free_games:
            shop = game.shop
            price = int(game.normal_price.replace("€", "").replace(".", ""))

            if self.is_game_new(game):
                avg_money = self.stats["average_money"]

                avg_money["total_money"] += price
                avg_money["maximum_price"] = max(avg_money["maximum_price"], price)

                shop_avg = next(
                    s for s in self.stats["average_money_store"] if s["name"] == shop
                )

                shop_avg["total_money"] += price
                shop_avg["maximum_price"] = max(shop_avg["maximum_price"], price)

    def update_allgames(self, free_games: list[Game]) -> None:
        """Updates the set of all games"""
        all_games = self.stats["all_games"]

        for game in free_games:
            name = game.name
            shop = game.shop
            all_games.add(f"{name}@{shop}")

    def update(self, free_games: list[Game], scan_successfull: bool) -> None:
        """Updates the statistic after a freegames scan."""
        self.timer.start("writing_statistics")

        self.stats = self.read_statistic_file()

        self.stats["total_scans"] += 1
        if scan_successfull:
            self.stats["average_success"]["success"] += 1
            self.update_money(free_games)
            self.update_allgames(free_games)
            self.update_scantime()
        else:
            self.stats["average_success"]["fails"] += 1

        self.write()
        self.timer.stop("writing_statistics", log=True)
