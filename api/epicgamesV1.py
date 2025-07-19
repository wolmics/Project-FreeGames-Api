import requests
from json import loads

from structures import Game


class Filters:
    def __init__(self) -> None:
        """A register of all Filters to check"""
        self.filter_register = [
            Filters.check_all_requirements,
            Filters.valid_offer_type,
            Filters.valid_discount_price,
            Filters.valid_slug,
        ]

    def filter_game(self, data_found: dict):
        """A function to go through all filters, and checks them"""
        for filter_function in self.filter_register:
            if not filter_function(data_found):
                return False
        return True

    @staticmethod
    def check_all_requirements(data_found: dict) -> bool:
        """A filter that checks if all data it needs is existing"""
        all_data = [
            "title",
            "description",
            "offerType",
            "keyImages",
            "discountPrice",
            "originalPrice",
        ]
        requires_one_slug = [
            "productSlug",
            "pageSlug",
        ]  # It's okay, if one of them is missing
        requires_one_expiration = ["expiryDate", "endDate"]

        for item in data_found:
            if item in all_data:
                all_data.remove(item)
            elif item in requires_one_slug:
                requires_one_slug.remove(item)
            elif item in requires_one_expiration:
                requires_one_expiration.remove(item)

        return (
            len(all_data) == 0
            and len(requires_one_slug) <= 1
            and len(requires_one_expiration) <= 1
        )

    @staticmethod
    def valid_offer_type(data_found: dict) -> bool:
        """A filter to check if the offerType is valid"""
        return (
            data_found["offerType"] == "OTHERS"
            or data_found["offerType"] == "BASE_GAME"
            or data_found["offerType"] == "EDITION"
        )

    @staticmethod
    def valid_discount_price(data_found: dict) -> bool:
        """A filter to check if the game is free"""

        return True if data_found["discountPrice"] == 0 else False

    @staticmethod
    def valid_original_price(data_found: dict) -> bool:
        """A filter to check if the game is normally not free"""
        return True if data_found["originalPrice"] > 0 else False

    @staticmethod
    def valid_slug(data_found: dict) -> bool:
        """A filter to check if the slug is valid, fixes weird bug where slug is empty."""
        print(data_found)
        slug = data_found.get("productSlug", None) or data_found.get("pageSlug", None)
        return True if slug and slug != "[]" else False


class Epicgames:
    def __init__(self) -> None:
        """Init of the Epicgames class"""
        self.filters = Filters()

    def main(self, url: str) -> list[Game]:
        """Gets all the data, filters it and returns it"""
        json_data = self.fetch_page(url)

        games = []
        for item in json_data["data"]["Catalog"]["searchStore"]["elements"]:
            data_dict = self.find_all_data(item)

            if self.filters.filter_game(data_dict):

                title = self.get_game_name(data_dict)
                description = self.get_game_description(data_dict)
                image = self.get_image_url(data_dict)

                url = self.get_game_link(data_dict)
                expiration = self.get_game_expiration(data_dict)

                normal_price = self.get_game_normal_price(data_dict)

                games.append(
                    Game(
                        name=title,
                        description=description,
                        link=url,
                        image=image,
                        expiration=expiration,
                        normal_price=normal_price,
                        shop="epicgames",
                    )
                )

        return games

    @staticmethod
    def search_json(data: dict, keyword: str) -> list:
        """Goes recursively through all things in the item dict"""
        result = []

        if isinstance(data, dict):
            # If data is a dictionary, check if the keyword is a key
            if keyword in data:
                result.append(data[keyword])

            # Recursively search through values of the dictionary
            for value in data.values():
                result.extend(Epicgames.search_json(value, keyword))

        elif isinstance(data, list):
            # If data is a list, recursively search each element
            for item in data:
                result.extend(Epicgames.search_json(item, keyword))

        return result

    def find_all_data(self, item: dict) -> dict:
        """Finds all data it needs"""
        data_needed = [
            "title",
            "id",
            "description",
            "offerType",
            "expiryDate",
            "endDate",
            "pageSlug",
            "productSlug",
            "discountPrice",
            "keyImages",
            "originalPrice",
        ]
        data_dict = {}

        for keyword in data_needed:
            data_found = self.search_json(item, keyword)

            if len(data_found) > 0 and all(value is not None for value in data_found):
                data_dict.update({keyword: data_found[0]})
        return data_dict

    @staticmethod
    def fetch_page(url: str) -> dict:
        """Gets all data from url"""
        page = requests.get(url)
        return loads(page.text)

    @staticmethod
    def get_game_name(data: dict) -> str:
        """Gets game name"""
        return data["title"]

    @staticmethod
    def get_image_url(data: dict) -> str:
        """Gets the Image of the game"""
        for imageItem in data["keyImages"]:
            if imageItem["type"] == "OfferImageWide":
                return imageItem["url"]
        return data["keyImages"][0].get("url")

    @staticmethod
    def get_game_link(data: dict) -> str:
        """Gets the game link"""
        if "pageSlug" in data.keys():
            return "https://store.epicgames.com/en-US/p/" + data["pageSlug"]
        else:
            return "https://store.epicgames.com/en-US/p/" + data["productSlug"]

    @staticmethod
    def get_game_expiration(data: dict) -> str:
        """Gets the games expiration date"""
        if "expiryDate" in data:
            expire = data["expiryDate"].split("T")[0]
        else:
            expire = data["endDate"].split("T")[0]

        return expire[8:10] + "." + expire[5:7] + "." + expire[0:4]

    @staticmethod
    def get_game_description(data: dict) -> str:
        """Gets the description"""
        return (
            data["description"]
            if len(data["description"]) > 15
            else Epicgames.get_game_description_advanced(data["productSlug"])
        )

    @staticmethod
    def get_game_normal_price(data: dict) -> str:
        """Gets the normal price of the game nicely formatted"""
        price = (
            str(data["originalPrice"])[:2] + "." + str(data["originalPrice"])[-2:] + "€"
        )
        return price

    @staticmethod
    def get_game_description_advanced(slug: str) -> str:
        """Gets the normal price of the game nicely formatted advanced"""
        url = (
            f"https://store-content.ak.epicgames.com/api/en-US/content/products/{slug}"
        )
        data = Epicgames.fetch_page(url)
        short_description = Epicgames.search_json(data, "shortDescription")

        return short_description if len(short_description) > 0 else ""


def scan():
    epicgames_object = Epicgames()
    return epicgames_object.main(
        "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions?locale=en-US&country=DE&allowCountries=DE"
    )


if __name__ == "__main__":
    print(scan())
