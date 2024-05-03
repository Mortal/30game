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
