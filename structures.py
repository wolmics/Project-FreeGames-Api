"""A file to save all data structures"""

from dataclasses import dataclass


@dataclass
class Game:
    """A class representing a game with many attributes."""

    name: str
    description: str

    link: str
    image: str

    expiration: str
    normal_price: str

    shop: str


@dataclass
class EpicgamesGraphql:
    """A class to save epicgames graphql requests."""

    get_price = """
    query {{
      Catalog {{
        searchStore(
          allowCountries: "DE"
          country: "DE"
          locale: "de-DE"
          count: 1
          keywords: "{game}"
        ) {{
          elements {{
            title
            price(country: "DE") {{
              totalPrice {{
                originalPrice
                discountPrice
              }}
            }}
          }}
        }}
      }}
    }}
    """

    get_game_info = """
    query {{
      Catalog {{
        searchStore(
          allowCountries: "DE"
          country: "DE"
          locale: "en-GB"
          keywords: "{game}"
          count: 1
        ) {{
          elements {{
            title
            description
            productSlug
            keyImages {{
              type
              url
            }}
            price(country: "DE") {{
              totalPrice {{
                fmtPrice(locale: "de-DE") {{
                  originalPrice
                  discountPrice
                }}
              }}
            }}
            promotions {{
              promotionalOffers {{
                promotionalOffers {{
                  startDate
                  endDate
                }}
              }}
            }}
            offerMappings {{
                pageSlug
            }}
          }}
        }}
      }}
    }}
    """
