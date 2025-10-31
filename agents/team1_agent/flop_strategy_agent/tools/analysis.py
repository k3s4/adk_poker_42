
from __future__ import annotations

from collections.abc import Iterable, Iterator
from collections import Counter
from concurrent.futures import Executor
from functools import partial
from itertools import (
    chain,
    combinations,
    permutations,
    product,
    repeat,
)
from operator import eq
from random import choices, sample
from typing import Any

from .hand import Hand
from .util import Card, Deck, max_or_none, RankOrder, Suit

__SUITS = Suit.CLUB, Suit.DIAMOND, Suit.HEART, Suit.SPADE


def __parse_range(
        raw_range: str,
        rank_order: RankOrder,
) -> Iterator[frozenset[Card]]:

    def index(r: str) -> int:
        return rank_order.index(r)

    def iterate(ss: Any) -> Iterator[frozenset[Card]]:
        for s0, s1 in ss:
            yield frozenset(Card.parse(f'{r0}{s0}{r1}{s1}'))

    def iterate_plus(s: str) -> Iterator[frozenset[Card]]:
        if r0 == r1:
            r = rank_order[-1]

            yield from __parse_range(f'{r0}{r1}{s}-{r}{r}{s}', rank_order)
        else:
            i0 = index(r0)
            i1 = index(r1)

            if i0 > i1:
                i0, i1 = i1, i0

            for r in rank_order[i0:i1]:
                yield from __parse_range(f'{rank_order[i1]}{r}{s}', rank_order)

    def iterate_interval(s: str) -> Iterator[frozenset[Card]]:
        i0 = index(r0)
        i1 = index(r1)
        i2 = index(r2)
        i3 = index(r3)

        if i1 - i0 != i3 - i2:
            raise ValueError(
                (
                    f'Pattern {repr(raw_range)} is invalid because the two'
                    ' pairs of ranks that bounds the dash-separated notation'
                    ' must be a shifted version of the other.'
                ),
            )

        if i0 > i2:
            i0, i1, i2, i3 = i2, i3, i0, i1

        for ra, rb in zip(
                rank_order[i0:i2 + 1],
                rank_order[i1:i3 + 1],
        ):
            yield from __parse_range(f'{ra}{rb}{s}', rank_order)

    match tuple(raw_range):
        case r0, r1:
            if r0 == r1:
                yield from iterate(combinations(__SUITS, 2))
            else:
                yield from iterate(product(__SUITS, repeat=2))
        case r0, r1, 's':
            if r0 != r1:
                yield from iterate(zip(__SUITS, __SUITS))
        case r0, r1, 'o':
            if r0 == r1:
                yield from __parse_range(f'{r0}{r1}', rank_order)
            else:
                yield from iterate(permutations(__SUITS, 2))
        case r0, r1, '+':
            yield from iterate_plus('')
        case r0, r1, 's', '+':
            yield from iterate_plus('s')
        case r0, r1, 'o', '+':
            yield from iterate_plus('o')
        case r0, r1, '-', r2, r3:
            yield from iterate_interval('')
        case r0, r1, 's', '-', r2, r3, 's':
            yield from iterate_interval('s')
        case r0, r1, 'o', '-', r2, r3, 'o':
            yield from iterate_interval('o')
        case _:
            yield frozenset(Card.parse(raw_range))


def parse_range(
        *raw_ranges: str,
        rank_order: RankOrder = RankOrder.STANDARD,
) -> set[frozenset[Card]]:
    """Parse the range."""
    raw_ranges = tuple(
        ' '.join(raw_ranges).replace(',', ' ').replace(';', ' ').split(),
    )
    range_ = set[frozenset[Card]]()

    for raw_range in raw_ranges:
        range_.update(__parse_range(raw_range, rank_order))

    return range_


def __calculate_equities_0(
        hole_cards: tuple[list[Card], ...],
        board_cards: list[Card],
        hole_dealing_count: int,
        board_dealing_count: int,
        deck_cards: list[Card],
        hand_types: tuple[type[Hand], ...],
) -> list[float]:
    hole_cards = tuple(map(list.copy, hole_cards))
    board_cards = board_cards.copy()
    sample_count = (
        (hole_dealing_count * len(hole_cards))
        - sum(map(len, hole_cards))
        + board_dealing_count
        - len(board_cards)
    )
    sampled_cards = sample(deck_cards, k=sample_count)
    begin = 0

    for i in range(len(hole_cards)):
        end = begin + hole_dealing_count - len(hole_cards[i])

        hole_cards[i].extend(sampled_cards[begin:end])

        assert len(hole_cards[i]) == hole_dealing_count

        begin = end

    board_cards.extend(sampled_cards[begin:])

    assert len(board_cards) == board_dealing_count

    equities = [0.0] * len(hole_cards)

    for hand_type in hand_types:
        hands = list(
            map(
                partial(hand_type.from_game_or_none, board_cards=board_cards),
                hole_cards,
            ),
        )
        max_hand = max_or_none(hands)
        statuses = list(map(partial(eq, max_hand), hands))
        increment = 1 / (len(hand_types) * sum(statuses))

        for i, status in enumerate(statuses):
            if status:
                equities[i] += increment

    return equities


def __calculate_equities_1(
        hole_cards: list[tuple[list[Card], ...]],
        board_cards: list[Card],
        hole_dealing_count: int,
        board_dealing_count: int,
        deck_cards: list[list[Card]],
        hand_types: tuple[type[Hand], ...],
        index: int,
) -> list[float]:
    return __calculate_equities_0(
        hole_cards[index],
        board_cards,
        hole_dealing_count,
        board_dealing_count,
        deck_cards[index],
        hand_types,
    )


def calculate_equities(
        hole_ranges: Iterable[Iterable[Iterable[Card]]],
        board_cards: Iterable[Card],
        hole_dealing_count: int,
        board_dealing_count: int,
        deck: Deck,
        hand_types: Iterable[type[Hand]],
        *,
        sample_count: int,
        executor: Executor | None = None,
) -> list[float]:
    """Calculate the equities."""
    hole_ranges = tuple(map(list, map(partial(map, list), hole_ranges)))
    board_cards = list(board_cards)
    hand_types = tuple(hand_types)
    hole_cards = []
    deck_cards = []

    for selection in product(*hole_ranges):
        counter = Counter(chain(chain.from_iterable(selection), board_cards))

        if all(map(partial(eq, 1), counter.values())):
            hole_cards.append(selection)
            deck_cards.append(list(set(deck) - counter.keys()))

    fn = partial(
        __calculate_equities_1,
        hole_cards,  # type: ignore[arg-type]
        board_cards,
        hole_dealing_count,
        board_dealing_count,
        deck_cards,
        hand_types,
    )
    mapper: Any = map if executor is None else executor.map
    indices = choices(range(len(hole_cards)), k=sample_count)
    equities = [0.0] * len(hole_ranges)

    for i, equity in chain.from_iterable(map(enumerate, mapper(fn, indices))):
        equities[i] += equity

    for i, equity in enumerate(equities):
        equities[i] = equity / sample_count

    return equities
