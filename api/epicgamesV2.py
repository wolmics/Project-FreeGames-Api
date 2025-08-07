"""File to get all free games from Epicgames with all their data"""

from urllib.parse import quote
from json import loads
import cloudscraper

from structures import Game, EpicgamesGraphql

GRAPHQL_BASE = "https://store.epicgames.com/graphql"
OFFER_URL = "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions?locale=en-US&country=DE&allowCountries=DE"


class Epicgames:
    """Class to get all free games from Epicgames with all their data."""

    def __init__(self):
        """Creates a session"""
        self.session = cloudscraper.create_scraper()

    def fetch_url(self, url: str) -> dict:
        """Fetches a page"""
        page = self.session.get(url)
        return loads(page.text)

    def make_query(self, query: str) -> dict:
        """Makes a request to Epicgames graphql api."""
        return self.session.post(GRAPHQL_BASE, json={"query": query}).json()

    def is_game_valid(self, title: str) -> bool:
        """Checks if the normal price isn't 0 and the current price is 0."""
        price = self.make_query(EpicgamesGraphql.get_price.format(game=title))
        explicit_prices = price["data"]["Catalog"]["searchStore"]["elements"][0][
            "price"
        ]["totalPrice"]
        return (
            explicit_prices["originalPrice"] != 0
            and explicit_prices["discountPrice"] == 0
        )

    def get_game_info(self, title: str) -> dict:
        """Makes a query to Epicgames graphql api and gets the raw data for a game."""
        raw_game_info = self.make_query(
            EpicgamesGraphql.get_game_info.format(game=title)
        )
        return raw_game_info["data"]["Catalog"]["searchStore"]["elements"][0]

    @staticmethod
    def create_game_link(game_info: dict) -> str:
        """Creates a game link from the game slug."""
        base_url = "https://store.epicgames.com/en-UK/p/"

        if game_info["productSlug"]:
            return base_url + game_info["productSlug"]
        if game_info["offerMappings"] and game_info["offerMappings"][0]["pageSlug"]:
            return (
                base_url
                + game_info["offerMappings"][0]["pageSlug"]
            )

        title = game_info["title"]
        slug = title.lower().replace(" ", "-")
        return base_url + quote(slug)

    @staticmethod
    def get_game_picture(game_info: dict) -> str:
        """Gets the OfferImageWide picture from the game info."""
        for picture in game_info["keyImages"]:
            if picture["type"] == "OfferImageWide":
                return picture["url"]
        return "No Image Found..."

    @staticmethod
    def get_expiration(game_info: dict) -> str:
        """Gets the expiration date from the game info and formats it."""
        raw_date = game_info["promotions"]["promotionalOffers"][0]["promotionalOffers"][
            0
        ]["endDate"]
        date = raw_date.split("T")[0].split("-")
        return f"{date[2]}.{date[1]}.{date[0]}"

    @staticmethod
    def get_normal_price(game_info: dict) -> str:
        """Returns the normal price of a game."""
        return (
            game_info["price"]["totalPrice"]["fmtPrice"]["originalPrice"]
            .replace("\xa0", "")
            .replace(",", ".")
        )

    def game_data(self, raw_game: dict) -> Game:
        """Creates a Game object from the raw data."""
        title = raw_game["title"]
        game_info = self.get_game_info(title)

        description = game_info["description"]
        link = self.create_game_link(game_info)
        picture = self.get_game_picture(game_info)

        expiration_date = self.get_expiration(game_info)
        normal_price = self.get_normal_price(game_info)

        shop = "epicgames"

        return Game(
            name=title,
            description=description,
            link=link,
            image=picture,
            expiration=expiration_date,
            normal_price=normal_price,
            shop=shop,
        )

    def run(self) -> list[Game]:
        """Gets all free games on Epicgames."""
        event_games = self.fetch_url(OFFER_URL)

        games = []
        for event_game in event_games["data"]["Catalog"]["searchStore"]["elements"]:
            if self.is_game_valid(event_game["title"]):
                game = self.game_data(event_game)
                games.append(game)

        return games


def scan() -> list[Game]:
    """Scans all current free games on Epicgames."""
    epicgames = Epicgames()
    return epicgames.run()


if __name__ == "__main__":
    print(scan())
