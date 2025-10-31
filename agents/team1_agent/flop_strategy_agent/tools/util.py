""":mod:`pokerkit.utilities` implements classes related to poker
utilities.

These utilities (helper constants, functions, classes, methods, etc.)
are used throughout the PokerKit project.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from enum import Enum, StrEnum, unique
from functools import partial
from itertools import product, starmap
from operator import is_not
from typing import Any, ClassVar, TypeVar


_T = TypeVar('_T')


@unique
class Rank(StrEnum):
    """The enum class for ranks."""

    ACE: str = 'A'
    DEUCE: str = '2'
    TREY: str = '3'
    FOUR: str = '4'
    FIVE: str = '5'
    SIX: str = '6'
    SEVEN: str = '7'
    EIGHT: str = '8'
    NINE: str = '9'
    TEN: str = 'T'
    JACK: str = 'J'
    QUEEN: str = 'Q'
    KING: str = 'K'
    UNKNOWN: str = '?'


@unique
class RankOrder(tuple[Rank, ...], Enum):
    """The enum class for ordering of ranks."""

    STANDARD: tuple[Rank, ...] = (
        Rank.DEUCE,
        Rank.TREY,
        Rank.FOUR,
        Rank.FIVE,
        Rank.SIX,
        Rank.SEVEN,
        Rank.EIGHT,
        Rank.NINE,
        Rank.TEN,
        Rank.JACK,
        Rank.QUEEN,
        Rank.KING,
        Rank.ACE,
    )
    """The standard ranks (from deuce to ace)."""


@unique
class Suit(StrEnum):
    """The enum class for suits."""

    CLUB: str = 'c'
    DIAMOND: str = 'd'
    HEART: str = 'h'
    SPADE: str = 's'
    UNKNOWN: str = '?'


@dataclass(frozen=True)
class Card:
    """The class for cards."""

    UNKNOWN: ClassVar[Card]
    rank: Rank
    suit: Suit

    @classmethod
    def get_ranks(cls, cards: CardsLike) -> Iterator[Rank]:
        """Return an iterator of the ranks of each card."""
        for card in cls.clean(cards):
            yield card.rank

    @classmethod
    def get_suits(cls, cards: CardsLike) -> Iterator[Suit]:
        """Return an iterator of the suits of each card."""
        for card in cls.clean(cards):
            yield card.suit

    @classmethod
    def are_suited(cls, cards: CardsLike) -> bool:
        """Return the suitedness of the given cards."""
        return len(set(cls.get_suits(cards))) <= 1

    @classmethod
    def are_rainbow(cls, cards: CardsLike) -> bool:
        """Return whether the cards are rainbow."""
        suits = tuple(cls.get_suits(cards))
        return len(set(suits)) == len(suits)

    @classmethod
    def clean(cls, values: CardsLike) -> tuple[Card, ...]:
        """Clean the cards."""
        if isinstance(values, Card):
            values = (values,)
        elif isinstance(values, str):
            values = tuple(Card.parse(values))
        elif isinstance(values, Iterable):
            assert not isinstance(values, str)
            values = tuple(values)
        else:
            raise ValueError(f'The card values {repr(values)} are invalid.')
        return values

    @classmethod
    def parse(cls, *raw_cards: str) -> Iterator[Card]:
        """Parse the string of the card representations."""
        for contents in raw_cards:
            contents = contents.replace('10', 'T').replace(',', '')
            for content in contents.split():
                if len(content) % 2 != 0:
                    raise ValueError(
                        (
                            'The sum of the lengths of valid card'
                            ' representations must be a multiple of 2, unlike'
                            f' {repr(content)}'
                        ),
                    )
                for i in range(0, len(content), 2):
                    rank = Rank(content[i])
                    suit = Suit(content[i + 1])
                    yield cls(rank, suit)

    def __repr__(self) -> str:
        return f'{self.rank}{self.suit}'

    def __str__(self) -> str:
        return f'{self.rank.name} OF {self.suit.name}S ({repr(self)})'


Card.UNKNOWN = Card(Rank.UNKNOWN, Suit.UNKNOWN)
CardsLike = Iterable[Card] | Card | str


@unique
class Deck(tuple[Card, ...], Enum):
    """The enum class for a tuple of cards representing decks."""

    STANDARD: tuple[Card, ...] = tuple(
        starmap(
            Card,
            product(
                RankOrder.STANDARD,
                (Suit.CLUB, Suit.DIAMOND, Suit.HEART, Suit.SPADE),
            ),
        ),
    )


def filter_none(values: Iterable[Any]) -> Any:
    """Filter out ``None`` from an iterable of values."""
    return filter(partial(is_not, None), values)


def max_or_none(values: Iterable[Any], key: Any = None) -> Any:
    """Get the maximum value while ignoring ``None`` values."""
    try:
        return max(filter_none(values), key=key)
    except ValueError:
        return None