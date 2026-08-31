"""Class to make statistics out of scanned free games"""

from dataclasses import dataclass, field, asdict
from json import dumps, loads
from typing import Optional

from structures import Game

from config import Config
from logger import setup_logger
from statistics import timer

logger = setup_logger(__name__)

STORES = ("steam", "epicgames", "gog")


@dataclass
class SuccessStats:
    success: int = 0
    fails: int = 0


@dataclass
class MoneyStats:
    total_money: int = 0
    maximum_price: int = 0


@dataclass
class StoreMoneyStats:
    name: str
    total_money: int = 0
    maximum_price: int = 0


@dataclass
class ScantimeStats:
    total_scantime: float = 0
    maximum_scantime: float = 0
    minimum_scantime: Optional[float] = None


@dataclass
class StoreScantimeStats:
    name: str
    total_scantime: float = 0
    maximum_scantime: float = 0
    minimum_scantime: Optional[float] = None


@dataclass
class StatisticsData:
    total_scans: int = 0
    average_success: SuccessStats = field(default_factory=SuccessStats)
    average_money: MoneyStats = field(default_factory=MoneyStats)
    average_money_store: list[StoreMoneyStats] = field(
        default_factory=lambda: [StoreMoneyStats(name=s) for s in STORES]
    )
    average_scantime: ScantimeStats = field(default_factory=ScantimeStats)
    average_scantime_store: list[StoreScantimeStats] = field(
        default_factory=lambda: [StoreScantimeStats(name=s) for s in STORES]
    )
    all_games: set[str] = field(default_factory=set)

    def to_json(self) -> str:
        """Serializes the statistics to a JSON string (set -> list for games)."""
        data = asdict(self)
        data["all_games"] = list(data["all_games"])
        return dumps(data, indent=4)

    @staticmethod
    def from_dict(data: dict) -> "StatisticsData":
        """Builds a StatisticsData object back from a plain dict (e.g. loaded JSON)."""
        return StatisticsData(
            total_scans=data["total_scans"],
            average_success=SuccessStats(**data["average_success"]),
            average_money=MoneyStats(**data["average_money"]),
            average_money_store=[
                StoreMoneyStats(**item) for item in data["average_money_store"]
            ],
            average_scantime=ScantimeStats(**data["average_scantime"]),
            average_scantime_store=[
                StoreScantimeStats(**item) for item in data["average_scantime_store"]
            ],
            all_games=set(data["all_games"]),
        )


class Statistics:
    """Class to make statistics for freegames api"""

    def __init__(self) -> None:
        """Sets up path"""
        self.stats: StatisticsData = StatisticsData()
        self.stats_dump: dict[str, float] = {}
        self.statistic_file = Config.get_destinations().output_folder / "statistics.json"
        self.timer = timer.Timer()

    def create_statistic_file(self) -> None:
        """Creates and writes a fresh data structure to the file"""
        self.statistic_file.write_text(StatisticsData().to_json(), encoding="utf-8")

    def read_statistic_file(self) -> StatisticsData:
        """Check if file exists, else create one. Then read it."""
        if not self.statistic_file.exists():
            self.create_statistic_file()

        data = loads(self.statistic_file.read_text(encoding="utf-8"))
        return StatisticsData.from_dict(data)

    def write(self) -> None:
        """Saves the current statistics to disk."""
        payload = self.stats.to_json()
        self.statistic_file.write_text(payload, encoding="utf-8")

        if Config.get_statistics().public_statistics:
            file_path = Config.get_destinations().public_output_folder / "statistics.json"
            file_path.write_text(payload, encoding="utf-8")

    def dump(self, key: str, value: float) -> None:
        """Dumps data into a dictionary."""
        self.stats_dump[key] = value

    def is_game_new(self, game: Game) -> bool:
        """Checks if game is in the all_games list."""
        return f"{game.name}@{game.shop}" not in self.stats.all_games

    def update_scantime(self) -> None:
        """Updates the scantime statistics."""
        total_duration = self.stats_dump["total_duration"]
        avg_stats = self.stats.average_scantime

        avg_stats.total_scantime += total_duration
        avg_stats.maximum_scantime = max(avg_stats.maximum_scantime, total_duration)
        avg_stats.minimum_scantime = (
            total_duration
            if avg_stats.minimum_scantime is None
            else min(avg_stats.minimum_scantime, total_duration)
        )

        for item in self.stats.average_scantime_store:
            duration = self.stats_dump[f"{item.name}_duration"]

            item.total_scantime += duration
            item.maximum_scantime = max(item.maximum_scantime, duration)
            item.minimum_scantime = (
                duration
                if item.minimum_scantime is None
                else min(item.minimum_scantime, duration)
            )

    def update_money(self, free_games: list[Game]) -> None:
        """Updates all the money items."""
        for game in free_games:
            if not self.is_game_new(game):
                continue

            price = int(game.normal_price.replace("€", "").replace(".", ""))

            avg_money = self.stats.average_money
            avg_money.total_money += price
            avg_money.maximum_price = max(avg_money.maximum_price, price)

            shop_avg = next(
                s for s in self.stats.average_money_store if s.name == game.shop
            )
            shop_avg.total_money += price
            shop_avg.maximum_price = max(shop_avg.maximum_price, price)

    def update_allgames(self, free_games: list[Game]) -> None:
        """Updates the set of all games"""
        for game in free_games:
            self.stats.all_games.add(f"{game.name}@{game.shop}")

    def update(self, free_games: list[Game], scan_successfull: bool) -> None:
        """Updates the statistic after a freegames scan."""
        self.timer.start("writing_statistics")

        self.stats = self.read_statistic_file()

        self.stats.total_scans += 1
        if scan_successfull:
            self.stats.average_success.success += 1
            self.update_money(free_games)
            self.update_allgames(free_games)
            self.update_scantime()
        else:
            self.stats.average_success.fails += 1

        self.write()
        self.timer.stop("writing_statistics", log=True)