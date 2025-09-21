import requests
from bs4 import BeautifulSoup
from datetime import datetime

from structures import Game

class Steam:
    def __init__(self):
        self.session = requests.Session()

        self.session.headers.update(
            {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36", "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7", }
        )

    def get(self, url):
        return self.session.get(url)

    def getFreeGames(self) -> list[Game]:
        games = []

        app_ids = self.getGameIds()

        for app_id in app_ids:
            data = self.getGameInfo(app_id)
            if data.get("type") == "game" and data.get("is_free") == True:

                title = data.get("name")
                description = data.get("short_description")
                link = f"https://store.steampowered.com/app/{app_id}"
                image = data.get("header_image")
                expiration = self.getGameExpiration(link)
                normal_price = data.get("price_overview").get("initial_formatted")

                games.append(Game(title, description, link, image, expiration, normal_price, "steam", ))

        return games

    def getGameIds(self) -> list[str]:
        app_ids = []

        resp = self.get('https://store.steampowered.com/search/results/?sort_by=_ASC&maxprice=free&supportedlang=english&specials=1&json=1').json()
        for item in resp.get("items", []):
            app_ids.append(item.get("logo", "").split("/apps/")[1].split("/")[0])

        return app_ids

    def getGameInfo(self, app_id):
        resp = self.get(f"https://store.steampowered.com/api/appdetails?appids={app_id}").json().get(app_id).get("data")
        return resp

    def getGameExpiration(self, link):
        text = self.get(link).text
        soup = BeautifulSoup(text, "html.parser")
        expiration = soup.find("p", class_="game_purchase_discount_quantity").text

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
    def transform_month(month: str) -> str:
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
        return str(months.get(month.lower()))

    @staticmethod
    def check_year(day: int, month: int) -> datetime.today:
        """Checks if the expiration is in the next year or not."""
        today = datetime.today()
        expiration_date_this_year = datetime(today.year, month, day)
        return today.year if today <= expiration_date_this_year else today.year + 1

def scan():
    s = Steam()
    return s.getFreeGames()

if __name__ == '__main__':
    print(scan())