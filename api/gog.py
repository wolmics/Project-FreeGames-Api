"""Files to get all free games from gog."""

from datetime import datetime, timedelta
from json import loads, dumps
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup

from config import Config
from structures import Game


class Gog:
    """Class to get all free games from gog."""

    @staticmethod
    def fetch_url(url):
        """Opens a website and returns BeautifulSoup object."""
        req = Request(
            url,
            headers={
                "Accept-Language": "en-US,en;q=0.9",
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/114.0.0.0 Safari/537.36"
                ),
            },
        )

        with urlopen(req) as response:
            return response.read().decode("utf-8")

    @staticmethod
    def create_soup(url: str) -> BeautifulSoup:
        """Opens a website and returns BeautifulSoup object."""
        content = Gog.fetch_url(url)
        return BeautifulSoup(content, "html.parser")

    @staticmethod
    def soup(url: str) -> list[Game]:
        """Returns a list of Game objects."""
        site = Gog.create_soup(url)

        giveaway_html = site.find(id="giveaway", class_="ng-star-inserted")

        if giveaway_html:

            link = giveaway_html.find(class_="giveaway__overlay-link")["href"]
            image = giveaway_html.find("source", class_="ng-star-inserted")[
                "srcset"
            ].split(" ")[1]
            name = giveaway_html.find("img", class_="ng-star-inserted")["alt"].replace(
                " giveaway", ""
            )

            expiration = Gog.expiration_cache()

            response = Gog.game_api_search(name)
            description = Gog.create_description(name, response)
            normal_price = Gog.get_normal_price(response)

            return [
                Game(
                    name=name,
                    description=description,
                    link=link,
                    image=image,
                    expiration=expiration,
                    normal_price=normal_price,
                    shop="gog",
                )
            ]

        Gog.clear_expiration()
        return []

    @staticmethod
    def game_api_search(name: str) -> dict:
        """Searches the game on the gog api."""
        game_slug = name.replace(" ", "+")
        response = Gog.fetch_url(
            "https://www.gog.com/games/ajax/filtered?mediaType=game&sort=popularity&page=1&search="
            + game_slug
        )
        return loads(response)

    @staticmethod
    def get_normal_price(response: dict) -> str:
        """Gets the normal price from Gog."""
        if response["totalGamesFound"] == 1:
            if response["products"][0]["price"]["amount"] != "0.00":
                return response["products"][0]["price"]["amount"] + "€"
            return response["products"][0]["price"]["baseAmount"] + "€"
        return ""

    @staticmethod
    def create_description(name: str, response: dict) -> str:
        """Creates the description out of information from the api response."""
        if response["totalGamesFound"] == 1:
            genres = response["products"][0]["genres"]
            developer = response["products"][0]["developer"]
            genre_str = ", ".join(genres)
            return f"{name} is a {genre_str.lower()} game developed by {developer}."
        return ""

    @staticmethod
    def expiration_cache() -> str:
        """For purpose of starting the 72-hour countdown for the expiration."""
        cache_file = Config.get_destinations().cache_folder / "gog.json"

        content = loads(cache_file.read_text(encoding="utf-8"))

        if content.get("expiration"):
            return content.get("expiration")

        end_date = datetime.now() + timedelta(days=3)
        dict_end_date = {"expiration": end_date.strftime("%d.%m.%Y")}

        cache_file.write_text(dumps(dict_end_date, indent=4), encoding="utf-8")

        return end_date.strftime("%d.%m.%Y")

    @staticmethod
    def clear_expiration() -> None:
        """Clearing cache."""
        cache_file = Config.get_destinations().cache_folder / "gog.json"
        cache_file.write_text(dumps({}), encoding="utf-8")


def scan() -> list[Game]:
    """Returns a list of Game objects."""
    gog_object = Gog()
    return gog_object.soup("https://www.gog.com/en/")


if __name__ == "__main__":
    print(scan())
