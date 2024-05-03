import fractions
import functools
from typing import Callable, Sequence

from rolls import outcomes


Strategy = Callable[[Sequence[int], int], Sequence[int]]
Utility = Callable[[int], int | fractions.Fraction]
RollValueFunction = Callable[[Sequence[int], int], int | fractions.Fraction]


def compute_values_single_row(n: int, dice_count: int, sides: int, strategy: Strategy, values: Sequence[Sequence[int | fractions.Fraction]]) -> Sequence[fractions.Fraction]:
    assert len(values) >= n-1
    assert n >= 1
    # What might the accumulated sum be at most with n dice remaining?
    max_sum = (dice_count - n) * (sides - 1)
    # At the end, tmp_value[s] will be k**n times the expected utility.
    tmp_value: list[int | fractions.Fraction] = [0 for s in range(max_sum + 1)]

    for outcome, multiplicity in outcomes(sides, n):
        outcome_sum = sum(outcome)
        for s in range(0, max_sum + 1):
            reroll = strategy(outcome, s)
            reroll_sum = sum(reroll)
            keep_sum = outcome_sum - reroll_sum
            reroll_value = values[len(reroll)][s + keep_sum]
            tmp_value[s] += multiplicity * reroll_value

    return [fractions.Fraction(a, sides ** n) for a in tmp_value]


def probability_to_reach(n: int, dice_count: int, sides: int, target: Sequence[Sequence[bool]], s: int = 0) -> tuple[fractions.Fraction, Sequence[tuple[int, Sequence[int]]]]:
    values = [[1 if t else 0 for t in row] for row in target]
    strategy = optimizing_strategy(dice_count, values)
    n_successes = 0
    good_outcomes: list[tuple[int, Sequence[int]]] = []
    for outcome, multiplicity in outcomes(sides, n):
        outcome_sum = sum(outcome)
        reroll = strategy(outcome, s)
        reroll_sum = sum(reroll)
        keep_sum = outcome_sum - reroll_sum
        reroll_value = values[len(reroll)][s + keep_sum]
        if reroll_value:
            good_outcomes.append((multiplicity, outcome))
            n_successes += multiplicity
    good_outcomes.sort()
    return fractions.Fraction(n_successes, sides ** n), good_outcomes


def compute_values(dice_count: int, sides: int, strategy: Strategy, utility: Utility) -> Sequence[Sequence[int | fractions.Fraction]]:
    # values[n][s] == v means that for n remaining dice,
    # accumulated sum s, the expected utility is v.
    values: list[Sequence[int | fractions.Fraction]] = []
    # Fill out "values" for n = 0 using the utility function.
    values.append([utility(s) for s in range(dice_count * (sides-1) + 1)])
    for n in range(1, dice_count + 1):
        values.append(compute_values_single_row(
            n, dice_count, sides, strategy, values))
    return values


def compute_value(dice_count: int, sides: int, strategy: Strategy, utility: Utility) -> int | fractions.Fraction:
    values = compute_values(dice_count, sides, strategy, utility)
    return values[dice_count][0]


def optimizing_strategy(dice_count: int, values: Sequence[Sequence[int | fractions.Fraction]]) -> Strategy:
    # What can we do with an outcome on n dice?
    # Reroll the first m (0 <= m < n) or the last m (1 <= m < n).
    rerolls = [
        [slice(0, m) for m in range(n)] +
        [slice(m, n) for m in range(1, n)]
        for n in range(dice_count + 1)]

    def reroll_strategy(outcome: Sequence[int], current_sum: int) -> Sequence[int]:
        """
        "outcome" is a list of length [1, dice_count] with dice in sorted
        order. Returns the subset of the dice to reroll.
        """
        outcome_sum = sum(outcome)
        best_reroll: slice | None
        best_reroll = best_value = None
        for reroll_slice in rerolls[len(outcome)]:
            reroll_sum = sum(outcome[reroll_slice])
            reroll_count = reroll_slice.stop - reroll_slice.start
            keep_sum = outcome_sum - reroll_sum
            # Suppose we had already accumulated "current_sum",
            # and now we keep another "keep_sum"
            # and reroll the "reroll_count" dice.
            reroll_value = values[reroll_count][current_sum + keep_sum]
            if best_reroll is None or best_value < reroll_value:
                best_reroll = reroll_slice
                best_value = reroll_value
        assert best_reroll is not None
        return outcome[best_reroll]

    return reroll_strategy


def values_max(*targets: Sequence[Sequence[int | fractions.Fraction]]) -> Sequence[Sequence[int | fractions.Fraction]]:
    values: list[Sequence[int | fractions.Fraction]] = []
    for n in range(len(targets[0])):
        target_rows = [target[n] for target in targets]
        values.append([max(target[n][s] for target in targets)
                       for s in range(len(targets[0][n]))])
    return values


def values_zip(*targets: Sequence[Sequence[int]]) -> Sequence[Sequence[int]]:
    values: list[Sequence[int]] = []
    for n in range(len(targets[0])):
        target_rows: Sequence[Sequence[int]] = [target[n] for target in targets]
        values.append(list(zip(*target_rows)))  # type: ignore
    return values


def optimizing_strategy_tiebreaks(*targets: Sequence[Sequence[int]]) -> Strategy:
    dice_count = len(targets[0]) - 1
    return optimizing_strategy(dice_count, values_zip(*targets))


def ensemble_of_optimizers(*targets: Sequence[Sequence[int]]) -> Strategy:
    dice_count = len(targets[0]) - 1
    return optimizing_strategy(dice_count, values_max(*targets))


def solve_game(dice_count: int, sides: int, utility: Utility) -> tuple[Sequence[Sequence[int | fractions.Fraction]], Strategy]:
    """
    Suppose we have n k-sided dice (sides 0, 1, ..., k-1)
    and we perform the following process:
    Throw the dice, and take out a non-empty subset of them,
    remembering the sum.  As long as you still have dice left, throw the
    remaining dice, and take out a non-empty subset of them, adding up their
    sum with what you already put aside.
    When you have no more dice, you have a resulting sum between 0 and n*(k-1)
    and you win utility(sum).
    What is the expected utility of the optimal strategy?

    >>> print(value(1, 6, lambda s: s))  # Expected throw
    5/2

    Probability of getting an even number:
    >>> print(value(1, 6, lambda s: 1 if s % 2 == 0 else 0))
    1/2
    """

    # values[n][s] == v means that for n remaining dice,
    # accumulated sum s, the expected utility is v.
    values: list[Sequence[int | fractions.Fraction]] = []

    # Fill out "values" for n = 0 using the utility function.
    values.append([utility(s) for s in range(dice_count * (sides-1) + 1)])

    reroll_strategy = optimizing_strategy(dice_count, values)

    for n in range(1, dice_count+1):
        values.append(compute_values_single_row(
            n, dice_count, sides, reroll_strategy, values))

    return values, reroll_strategy


def value(dice_count: int, sides: int, utility: Utility) -> int | fractions.Fraction:
    return solve_game(dice_count, sides, utility)[0][dice_count][0]


def optimal_values(dice_count: int, sides: int, utility: Utility) -> Sequence[Sequence[int | fractions.Fraction]]:
    return solve_game(dice_count, sides, utility)[0]


def compute_strategy(dice_count: int, sides: int, utility: Utility) -> Strategy:
    return solve_game(dice_count, sides, utility)[1]


def roll_value_function(values: Sequence[Sequence[int | fractions.Fraction]], strategy: Strategy) -> RollValueFunction:
    def roll_value(roll_z: Sequence[int], current_sum: int = 0) -> int | fractions.Fraction:
        roll_sum = sum(roll_z)
        reroll = strategy(roll_z, 0)
        reroll_sum = sum(reroll)
        keep_sum = roll_sum - reroll_sum
        return values[len(reroll)][current_sum + keep_sum]

    return roll_value
