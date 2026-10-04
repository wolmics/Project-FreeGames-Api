import requests
import re
import html
from datetime import datetime, timezone

from structures import Game

sections_api = "https://sections.gog.com/v1/pages/2f?countryCode={country_code}&locale={locale}&currencyCode={currency_code}"
giveaway_api = "https://sections.gog.com/v1/pages/2f/sections/{sectionId}?countryCode={country_code}&locale={locale}&currencyCode={currency_code}"

class GoodOldGames:
    """Class to get free games from Good old Games."""
    def __init__(self, country_code: str = "DE", locale: str = "en-US", currency_code: str = "EUR"):
        self.country_code = country_code
        self.locale = locale
        self.currency_code = currency_code

    def get_free_games(self) -> list[Game]:
        section_ids = self.get_section_ids()

        games = []
        for section_id in section_ids:
            raw_data = self.get_game(section_id)
            raw_game = raw_data["product"]

            games.append(
                Game(
                    name = raw_game["title"],
                    description = self.get_description(raw_game["id"]),
                    link = "https://www.gog.com/de/game/" + raw_game["slug"],
                    image = raw_game["coverHorizontal"],
                    expiration = self.get_expiration(raw_data["endDate"]),
                    normal_price = self.get_price(raw_game),
                    shop = "gog",
                )
            )
        return games

    def get_section_ids(self) -> list[str]:
        request_url = sections_api.format(
            country_code=self.country_code,
            locale=self.locale,
            currency_code=self.currency_code
        )

        response = requests.get(request_url).json()
        sections = response["sections"]

        section_ids = []
        for section in sections:
            if section["sectionType"] == "GIVEAWAY_SECTION":
                section_ids.append(section["sectionId"])

        return section_ids

    def get_game(self, section_id: str) -> dict:
        request_url = giveaway_api.format(
            sectionId=section_id,
            country_code=self.country_code,
            locale=self.locale,
            currency_code=self.currency_code
        )
        response = requests.get(request_url).json()

        return response["properties"]

    def get_description(self, game_id: str) -> str:
        response = requests.get(f"https://api.gog.com/products/{game_id}", params={"expand": "description", "locale": self.locale, }, timeout=15, )
        response.raise_for_status()

        description = response.json()["description"]["lead"]

        # Replace HTML tags with spaces and decode entities such as &amp;
        description = re.sub(r"<[^>]+>", " ", description)
        description = html.unescape(description)

        # Collapse newlines and repeated whitespace
        return re.sub(r"\s+", " ", description).strip()

    @staticmethod
    def get_price(raw_game) -> str:
        price = raw_game["price"]["baseMoney"]["amount"]
        return price + "€"

    @staticmethod
    def get_expiration(raw_date: str) -> str:
        dt = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
        dt = dt.astimezone(timezone.utc)
        return dt.replace(microsecond=0).isoformat()

def scan() -> list[Game]:
    """Returns a list of Game objects."""
    gog_object = GoodOldGames()
    return gog_object.get_free_games()


if __name__ == "__main__":
    print(scan())
