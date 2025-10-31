"""mod:`pokerkit.hands` implements classes related to poker hands."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Hashable
from functools import total_ordering
from itertools import chain, combinations
from typing import Any, ClassVar

from .lookup import (
    Entry,
    Lookup,
    StandardLookup,
)
from .util import Card, CardsLike


@total_ordering
class Hand(Hashable, ABC):
    """The abstract base class for poker hands."""

    lookup: ClassVar[Lookup]
    low: ClassVar[bool]

    @classmethod
    @abstractmethod
    def from_game(
            cls,
            hole_cards: CardsLike,
            board_cards: CardsLike = (),
    ) -> Hand:
        """Create a poker hand from a game setting."""
        pass  # pragma: no cover

    @classmethod
    def from_game_or_none(
            cls,
            hole_cards: CardsLike,
            board_cards: CardsLike = (),
    ) -> Hand | None:
        """Create a poker hand from a game setting or return ``None``."""
        try:
            hand = cls.from_game(hole_cards, board_cards)
        except ValueError:
            hand = None

        return hand

    def __init__(self, cards: CardsLike) -> None:
        self.__cards = Card.clean(cards)

        if not self.lookup.has_entry(self.cards):
            raise ValueError(
                (
                    f'The cards {repr(cards)} form an invalid'
                    f' {type(self).__qualname__} hand.'
                ),
            )

    def __eq__(self, other: Any) -> bool:
        if type(self) != type(other):  # noqa: E721
            return NotImplemented

        assert isinstance(other, Hand)

        return self.entry == other.entry

    def __hash__(self) -> int:
        return hash(self.entry)

    def __lt__(self, other: Hand) -> bool:
        if type(self) != type(other):  # noqa: E721
            return NotImplemented

        assert isinstance(other, Hand)

        if self.low:
            ordering = self.entry > other.entry
        else:
            ordering = self.entry < other.entry

        return ordering

    def __repr__(self) -> str:
        return ''.join(map(repr, self.cards))

    def __str__(self) -> str:
        return f'{self.entry.label.value} ({repr(self)})'

    @property
    def cards(self) -> tuple[Card, ...]:
        """Return the cards that form this hand."""
        return self.__cards

    @property
    def entry(self) -> Entry:
        """Return the hand entry."""
        return self.lookup.get_entry(self.cards)


class StandardHighHand(Hand):
    """The class for standard high hands."""

    lookup = StandardLookup()
    card_count = 5
    low = False

    @classmethod
    def from_game(
            cls,
            hole_cards: CardsLike,
            board_cards: CardsLike = (),
    ) -> Hand:
        """Create a poker hand from a game setting."""
        max_hand = None

        for combination in combinations(
                chain(Card.clean(hole_cards), Card.clean(board_cards)),
                cls.card_count,
        ):
            try:
                hand = cls(combination)
            except ValueError:
                pass
            else:
                if max_hand is None or hand > max_hand:
                    max_hand = hand

        if max_hand is None:
            raise ValueError(
                (
                    f'No valid {cls.__qualname__} hand can be formed'
                    ' from the hole and board cards.'
                ),
            )

        return max_hand