import argparse
import itertools
from typing import Callable

from descriptions import describe_keep_reroll
from policyeval import (
    RollValueFunction,
    Utility,
    roll_value_function,
    solve_game,
)


def my_utility(s: int) -> int:
    opponents = 3
    lose_factor = -1
    max_lose = 14
    strictly_below = 10 * opponents
    dead_on = 2 * opponents
    above = [4, 8, 12, 16, 20, 24]

    # "Skarpt under 11" => strictly less than 5
    # "30" => 24
    if s < 5:
        return strictly_below
    elif s < 24:
        # return 24 - s
        return lose_factor * min(max_lose, (24 - s))
    elif s == 24:
        return dead_on
    else:
        return above[s - 25]


def roll_value_optimal(
    dice_count: int, sides: int, utility: Utility
) -> RollValueFunction:
    values, strategy = solve_game(dice_count, sides, utility)
    return roll_value_function(values, strategy)


def input_roll(
    dice_count: int, sides: int, input: Callable[[str], str] = input
) -> list[int]:
    while True:
        try:
            roll_str = input("Input your roll: ")
        except (KeyboardInterrupt, EOFError):
            print("")
            raise SystemExit()
        roll_split = roll_str.split()
        if len(roll_split) == 1:
            roll_split = list(roll_split[0])
        try:
            roll = [int(v) for v in roll_split]
        except ValueError:
            print("Hmm, try again.")
            continue
        if len(roll) > dice_count:
            print("You can only roll %s dice at a time!" % dice_count)
            continue
        if not all(1 <= v <= sides for v in roll):
            print("Those are not the %s-sided dice I know!" % sides)
            continue
        if len(roll) <= 1:
            print("Looks like you're done!")
            continue
        return roll


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.parse_args()

    dice_count = 6
    sides = 6

    is_below = lambda s: 1 if s < 5 else 0  # noqa
    is_above = lambda s: 1 if s >= 24 else 0  # noqa
    is_win = lambda s: is_below(s) or is_above(s)  # noqa

    print(
        "Compute utility-maximizing strategy for %d %d-sided dice..."
        % (dice_count, sides)
    )
    values, strategy = solve_game(dice_count, sides, my_utility)

    below_max_prob = roll_value_optimal(dice_count, sides, is_below)
    above_max_prob = roll_value_optimal(dice_count, sides, is_above)
    while True:
        roll: list[int] = input_roll(dice_count, sides)
        min_sum = dice_count - len(roll)
        max_sum = (dice_count - len(roll)) * sides
        roll.sort()
        roll_z = [v - 1 for v in roll]
        rerolls = [
            describe_keep_reroll(dice_count, sides, strategy, roll, s)
            for s in range(min_sum, max_sum + 1)
        ]
        if min_sum == max_sum:
            (reroll,) = rerolls
            print("I would %s" % reroll)
            print(
                "If you decide to go under, your chance is at most "
                + "{:.2%}.\n".format(float(below_max_prob(roll_z, 0)))
                + "Otherwise, your chance is at most {:.2%}.".format(
                    float(above_max_prob(roll_z, 0))
                )
            )
        else:
            i = min_sum
            for reroll, ss in itertools.groupby(rerolls):
                j = i + len(list(ss))
                if i == min_sum and j == max_sum + 1:
                    print("I would %s" % reroll)
                elif i == j - 1:
                    print("If you have %s, I would %s" % (i, reroll))
                else:
                    print(
                        "If you have between %s and %s, I would %s" % (i, j - 1, reroll)
                    )
                i = j


if __name__ == "__main__":
    main()
