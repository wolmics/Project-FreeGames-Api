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