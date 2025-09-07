"""A script to get all discounted free games on steam"""

from urllib.request import urlopen
from datetime import datetime
from bs4 import BeautifulSoup

from structures import Game


class Steam:
    """Main class to get discounted free games"""

    @staticmethod
    def create_soup(url: str) -> BeautifulSoup:
        """Opens a site and returns BeautifulSoup object"""
        with urlopen(url) as response:
            return BeautifulSoup(response.read(), "html.parser")

    @staticmethod
    def soup(steam_url: str) -> list[Game]:
        """Main function to get all discounted free games"""
        games = []

        steam_site = Steam.create_soup(steam_url)

        results = steam_site.find(id="search_results")
        game_items = results.find_all("a")

        for item in game_items:
            if item.find("div", class_="discount_final_price").text == "0,00€":
                name = item.find("span", class_="title").text
                link = item.get("href")

                game_page = Steam.create_soup(link)
                if "This content requires the base game" in str(
                    game_page.find(
                        "div", class_="game_area_bubble game_area_dlc_bubble"
                    )
                ):
                    continue

                description = game_page.find(
                    "div", class_="game_description_snippet"
                ).text.strip()
                normal_price = Steam.get_original_price(game_page)

                image = game_page.find("img", class_="game_header_image_full").get(
                    "src"
                )
                expiration = Steam.get_expiration(game_page)

                games.append(
                    Game(
                        name,
                        description,
                        link,
                        image,
                        expiration,
                        normal_price,
                        "steam",
                    )
                )

        return games

    @staticmethod
    def get_expiration(game_page: BeautifulSoup) -> str:
        """Gets the game expiration date and formats it"""
        expiration = game_page.find("p", class_="game_purchase_discount_quantity").text
        trimmed_expiration = Steam.trim_date(expiration)

        day = Steam.get_day(trimmed_expiration)
        month = Steam.transform_month(trimmed_expiration[1])
        year = Steam.check_year(int(day), int(month))

        return str(day) + "." + str(month) + "." + str(year)

    @staticmethod
    def trim_date(expiration: str) -> list[str]:
        """Trims the expiration date out of the text"""
        expiration = expiration.split(" ")

        tmp_index1, tmp_index2 = 0, 0

        # Gets the first index of the list which is a number (The date) and the last index (@)
        for i in expiration:
            if i.isnumeric():
                tmp_index1 = expiration.index(i)
            elif i == "@":
                tmp_index2 = expiration.index(i)

        return expiration[tmp_index1:tmp_index2]

    @staticmethod
    def get_day(expiration: list[str]) -> str:
        """Gets the day of the expiration"""
        if len(expiration[0]) == 1:
            return "0" + expiration[0]
        return expiration[0]

    @staticmethod
    def transform_month(month: str) -> int:
        """Transforms the month to a number."""
        months = {
            "jan": "01",
            "feb": "02",
            "mar": "03",
            "apr": "04",
            "may": "05",
            "jun": "06",
            "jul": "07",
            "aug": "08",
            "sep": "09",
            "oct": "10",
            "nov": "11",
            "dec": "12",
        }
        return int(months.get(month.lower()))

    @staticmethod
    def check_year(day: int, month: int) -> datetime.today:
        """Checks if the expiration is in the next year or not."""
        today = datetime.today()
        expiration_date_this_year = datetime(today.year, month, day)
        return today.year if today <= expiration_date_this_year else today.year + 1

    @staticmethod
    def get_original_price(game_page: BeautifulSoup) -> str:
        """Return the original price of the game from the game page."""
        wrappers = game_page.find_all("div", class_="game_area_purchase_game_wrapper")

        for wrapper in wrappers:
            price_tag = wrapper.find("div", class_="discount_original_price")
            if price_tag and price_tag.text.strip():
                return price_tag.text.replace(",", ".").replace("-", "0").strip()

        return ""


def scan() -> list[Game]:
    """Returns a list of Game objects."""
    return Steam.soup(
        "https://store.steampowered.com/search/?maxprice=free&specials=1&ndl=1"
    )


if __name__ == "__main__":
    print(scan())
