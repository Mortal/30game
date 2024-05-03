import collections
import functools
import itertools
import operator
from math import factorial
from typing import Iterable, Iterator, Sequence


def product(iterable: Iterable[int]) -> int:
    return functools.reduce(operator.mul, iterable, 1)


def permutations(s: Iterable[int]) -> int:
    """
    >>> permutations('cat')
    6
    >>> permutations('mom')
    3
    """
    counts = collections.Counter(s)
    n = sum(counts.values())
    return factorial(n) // product(map(factorial, counts.values()))


def outcomes(sides: int, dice_count: int) -> Iterator[tuple[Sequence[int], int]]:
    outcomes_ = itertools.combinations_with_replacement(range(sides), dice_count)
    n_outcomes = 0
    n_distinct = 0
    for outcome in outcomes_:
        multiplicity = permutations(outcome)
        n_outcomes += multiplicity
        n_distinct += 1
        yield outcome, multiplicity
    assert n_outcomes == sides**dice_count
    assert n_distinct == (
        factorial(dice_count + sides - 1)
        // (factorial(dice_count) * factorial(sides - 1))
    )


def combinations_summing_to(
    sides: int, dice_count: int, s: int, suffix: tuple[int, ...] = ()
) -> Iterable[Sequence[int]]:
    """
    >>> print(list(combinations_summing_to(6, 4, 2)))
    [(0, 0, 0, 2), (0, 0, 1, 1)]
    >>> print(list(combinations_summing_to(6, 3, 5)))
    [(0, 0, 5), (0, 1, 4), (0, 2, 3), (1, 1, 3), (1, 2, 2)]
    >>> print(list(combinations_summing_to(6, 3, 12)))
    [(2, 5, 5), (3, 4, 5), (4, 4, 4)]
    """
    if dice_count == 0:
        return (suffix,) if s == 0 else ()
    elif dice_count == 1:
        return ((s,) + suffix,) if 0 <= s < sides else ()
    else:
        return itertools.chain.from_iterable(
            # Combinations summing to s where the last die shows k
            combinations_summing_to(k + 1, dice_count - 1, s - k, (k,) + suffix)
            for k in range(sides - 1, -1, -1)
            # Early bailout if you can't make s with all dice showing <= k
            if 0 <= s <= k * dice_count
        )


def outcomes_containing_subset(
    sides: int, dice_count: int, subset: Iterable[int]
) -> int:
    """
    >>> outcomes_containing_subset(3, 3, [0, 0, 0])
    1
    >>> outcomes_containing_subset(3, 3, [0, 0, 1])
    3
    >>> outcomes = [(0, 0, 0), (0, 0, 1), (0, 0, 2), (0, 1, 0), (0, 2, 0),
    ...             (1, 0, 0), (2, 0, 0)]
    >>> outcomes_containing_subset(3, 3, [0, 0]) == len(outcomes)
    True
    >>> outcomes_containing_subset(3, 3, [0]) == 3 ** 3 - 2 ** 3
    True
    """
    c = +collections.Counter(subset)
    if sum(c.values()) == dice_count:
        return permutations(c)
    else:
        r = 0
        for k in range(sides):
            if k in c:
                c2 = collections.Counter(c)
                c2.subtract([k])
                r += outcomes_containing_subset(sides, dice_count - 1, c2)
        unused = sides - len(c)
        if unused > 0:
            r += unused * outcomes_containing_subset(sides, dice_count - 1, c)
        return r


def outcomes_summing_to(
    sides: int, dice_count: int, n: int, s: int
) -> Iterator[tuple[Sequence[int], int]]:
    """
    >>> (outcome, multiplicity), = outcomes_summing_to(6, 6, 1, 4)
    >>> outcome
    (4,)
    >>> multiplicity == 6 ** 6 - 5 ** 6
    True
    """
    outcomes = combinations_summing_to(sides, n, s)
    for outcome in outcomes:
        multiplicity = outcomes_containing_subset(sides, dice_count, outcome)
        yield outcome, multiplicity


def subsequences(
    sequence: Sequence[int], prefix: tuple[int, ...] = ()
) -> tuple[tuple[int, ...], ...]:
    """
    >>> print(subsequences((1, 1, 2, 2)))
    ((1, 1, 2, 2), (1, 1, 2), (1, 1), (1, 2, 2), (1, 2), (1,), (2, 2), (2,), ())
    """
    if not sequence:
        return (prefix,)
    v = sequence[0]
    i = 1
    while i < len(sequence) and sequence[i] == v:
        i += 1
    return subsequences(sequence[1:], prefix + (v,)) + subsequences(
        sequence[i:], prefix
    )
