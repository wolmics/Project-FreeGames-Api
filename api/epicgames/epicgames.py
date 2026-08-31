"""Class to make statistics out of scanned free games"""
import time
from datetime import datetime, timezone
from urllib.parse import quote

import cloudscraper

from structures import Game

from api.epicgames.epicgames_graphql import GRAPHQL_URL, SCAN_QUERY, DETAILS_QUERY

class EpicgamesGraphql:
    """Scans Epic Games Store promotions for games that are normally paid
    but are currently free (excludes permanently free-to-play games)."""

    def __init__(self):
        self.scraper = self._build_scraper()

    # Setup

    @staticmethod
    def _build_scraper():
        scraper = cloudscraper.create_scraper(
            browser={
                "browser": "chrome",
                "platform": "windows",
                "desktop": True,
                "mobile": False,
            },
            interpreter="native",
            delay=None,
            allow_brotli=True,
        )

        scraper.headers.update(
            {
                "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
                "Origin": "https://store.epicgames.com",
                "Referer": "https://store.epicgames.com/de/free-games",
            }
        )

        return scraper

    # Public API

    def get_free_games(self, country_code: str = "DE", locale="de-DE") -> list:
        """Returns a list of Game objects for all currently free promotions."""
        raw_candidates = self._fetch_zero_priced_games(country=country_code, locale=locale)
        free_games = [e for e in raw_candidates if self._is_actually_free(e)]

        games = []
        for candidate in free_games:
            info = self._fetch_game_information(candidate.get("namespace"), candidate.get("id"), country_code, locale)
            if info is None:
                continue
            games.append(self._extract_game_data(info))

        return games

    # Fetching

    def _fetch_zero_priced_games(self, country, locale, page_size=40) -> list:
        """Pages through the store search for promotions flagged as free games."""
        elements = []
        start = 0

        while True:
            variables = {
                "allowCountries": country,
                "category": "games/edition/base|bundles/games|editors|software",
                "country": country,
                "locale": locale,
                "sortBy": "title",
                "sortDir": "ASC",
                "count": page_size,
                "start": start,
                "withPrice": True,
                "withPromotions": True,
                "freeGame": True,
            }

            resp = self.scraper.post(
                GRAPHQL_URL,
                json={"query": SCAN_QUERY, "variables": variables},
                headers={"Content-Type": "application/json", "Accept": "application/json"},
                timeout=20,
            )
            resp.raise_for_status()
            payload = resp.json()["data"]["Catalog"]["searchStore"]

            batch = payload["elements"]
            elements.extend(batch)
            start += len(batch)

            reached_total = start >= payload["paging"]["total"]
            if not batch or reached_total:
                break

            time.sleep(0.0)

        return elements

    def _fetch_game_information(self, namespace: str, offer_id: str, country: str, locale: str):
        """Fetches full details for a single game by namespace + offer id."""
        variables = {
            "sandboxId": namespace,
            "offerId": offer_id,
            "locale": locale,
            "country": country,
        }

        resp = self.scraper.post(GRAPHQL_URL, json={"query": DETAILS_QUERY, "variables": variables}, timeout=20)
        resp.raise_for_status()
        data = resp.json()

        if data.get("errors"):
            print(f"[error] namespace={namespace} id={offer_id}: {data['errors']}")
            return None

        return data["data"]["Catalog"]["catalogOffer"]

    # Parsing

    def _extract_game_data(self, game_info: dict) -> Game:
        """Builds a Game object from raw catalog offer data."""
        return Game(
            name=game_info["title"],
            description=game_info["description"],
            link=self._create_game_link(game_info),
            image=self._get_game_picture(game_info),
            expiration=self._get_expiration(game_info),
            normal_price=self._get_normal_price(game_info),
            shop="epicgames",
        )

    @staticmethod
    def _is_actually_free(element: dict) -> bool:
        """Excludes permanent F2P games (originalPrice == 0 too)."""
        total_price = (element.get("price") or {}).get("totalPrice") or {}
        original_price = total_price.get("originalPrice")
        discount_price = total_price.get("discountPrice")
        return original_price not in (None, 0) and discount_price == 0

    @staticmethod
    def _create_game_link(game_info: dict) -> str:
        """Builds the store URL for a game from its slug."""
        base_url = "https://store.epicgames.com/en-UK/p/"

        offer_mappings = game_info["offerMappings"]
        slug = (
            game_info["productSlug"]
            or (offer_mappings[0]["pageSlug"] if offer_mappings else None)
            or quote(game_info["title"].lower().replace(" ", "-"))
        )
        return base_url + slug

    @staticmethod
    def _get_game_picture(game_info: dict) -> str:
        """Returns the OfferImageWide picture URL, if one exists."""
        for picture in game_info["keyImages"]:
            if picture["type"] == "OfferImageWide":
                return picture["url"]
        return "No Image Found..."

    @staticmethod
    def _get_expiration(game_info: dict) -> str:
        """Returns the promotion's end date as an ISO 8601 UTC string."""
        raw_date = game_info["promotions"]["promotionalOffers"][0]["promotionalOffers"][0]["endDate"]

        dt = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
        dt = dt.astimezone(timezone.utc)

        return dt.isoformat()

    @staticmethod
    def _get_normal_price(game_info: dict) -> str:
        """Returns the formatted normal (non-discounted) price."""
        return (
            game_info["price"]["totalPrice"]["fmtPrice"]["originalPrice"]
            .replace("\xa0", "")
            .replace(",", ".")
        )


def scan() -> list[Game]:
    epicgames = EpicgamesGraphql()
    return epicgames.get_free_games()

if __name__ == "__main__":
    print(scan())
