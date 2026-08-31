import json
from datetime import datetime, timezone

import requests

from structures import Game


class Steam:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
                )
            }
        )

    def _get(self, url, params=None):
        return self.session.get(url, params=params)

    def get_free_games(self, country_code: str = "DE") -> list[Game]:
        """Returns a list of free (100%-off / free-to-keep) games from Steam."""
        app_ids = self.get_game_ids()
        if not app_ids:
            return []

        items = self.get_store_items(app_ids, country_code=country_code)

        games = []
        for item in items:
            # type 0 == k_EStoreAppType_Game
            if item.get("type") != 0 or not item.get("is_free", False):
                continue

            appid = item.get("appid")
            basic_info = item.get("basic_info", {})
            assets = item.get("assets", {})
            purchase_option = item.get("best_purchase_option", {})

            title = item.get("name")
            description = basic_info.get("short_description")
            link = f"https://store.steampowered.com/app/{appid}"
            image = f"https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/{appid}/{assets.get('header_2x')}"
            normal_price = purchase_option.get("formatted_original_price")
            expiration = self.get_expiration(purchase_option)

            games.append(
                Game(title, description, link, image, expiration, normal_price, "steam")
            )

        return games

    def get_game_ids(self) -> list[str]:
        """Fetches app IDs of currently free-on-sale games from the store search."""
        app_ids = []

        resp = self._get(
            "https://store.steampowered.com/search/results/",
            params={
                "sort_by": "_ASC",
                "maxprice": "free",
                "supportedlang": "english",
                "specials": 1,
                "json": 1,
            },
        ).json()

        for entry in resp.get("items", []):
            logo = entry.get("logo", "")
            if "/apps/" in logo:
                app_ids.append(logo.split("/apps/")[1].split("/")[0])

        return app_ids

    def get_store_items(self, app_ids: list[str], country_code: str = "DE") -> list[dict]:
        """Fetches store data (name, description, header image, price, active discounts, free-to-keep window)"""
        payload = {
            "ids": [{"appid": int(app_id)} for app_id in app_ids],
            "context": {
                "language": "english",
                "country_code": country_code,
                "steam_realm": 1,
            },
            "data_request": {
                "include_basic_info": True,
                "include_assets": True,
                "include_all_purchase_options": True,
            },
        }

        resp = self._get(
            "https://api.steampowered.com/IStoreBrowseService/GetItems/v1/",
            params={"input_json": json.dumps(payload)},
        ).json()

        return resp.get("response", {}).get("store_items", [])

    @staticmethod
    def get_expiration(purchase_option: dict) -> str | None:
        """ Expiration date in ISO 8601 format """
        timestamp = purchase_option.get("free_to_keep_ends")
        if not timestamp:
            discounts = purchase_option.get("active_discounts") or []
            if discounts:
                timestamp = discounts[0].get("discount_end_date")
        if not timestamp:
            return None

        dt_utc = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        # ISO 8601, unambiguous, sortable, carries the UTC offset
        return dt_utc.isoformat()


def scan():
    s = Steam()
    return s.get_free_games()


if __name__ == "__main__":
    print(scan())