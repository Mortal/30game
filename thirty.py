import random
import argparse
import operator
import itertools
from policyeval import (
    probability_to_reach, compute_values, compute_value, optimizing_strategy,
    values_max, solve_game, optimal_values, roll_value_function,
)
from descriptions import describe_strategy, describe_keep_reroll


def play_game(dice_count, sides, strategy):
    outcome = sorted(random.randrange(sides) for _ in range(dice_count))
    s = 0
    while outcome:
        print("Sum: %2d  You roll: %s -> %s" %
              (s + dice_count - len(outcome),
               [a + 1 for a in outcome],
               s + dice_count + sum(outcome)))
        reroll = strategy(outcome, s)
        outcome_sum = sum(outcome)
        reroll_sum = sum(reroll)
        keep_sum = outcome_sum - reroll_sum
        s += keep_sum
        if reroll:
            print("Sum: %2d  You chose to reroll: %s" %
                  (s + dice_count - len(reroll),
                   [a + 1 for a in reroll]))
        outcome = sorted(random.randrange(sides) for _ in range(len(reroll)))
    return s


def my_utility(s):
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


def roll_value_optimal(dice_count, sides, utility):
    values, strategy = solve_game(dice_count, sides, utility)
    return roll_value_function(values, strategy)


def roll_value_fixed(dice_count, sides, strategy, utility):
    values = compute_values(dice_count, sides, strategy, utility)
    return roll_value_function(values, strategy)


def input_roll(dice_count, sides, input=input):
    while True:
        try:
            roll_str = input('Input your roll: ')
        except (KeyboardInterrupt, EOFError):
            print('')
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--infiniplay', action='store_true')
    parser.add_argument('-d', '--describe', action='store_true')
    parser.add_argument('-l', '--lucky', action='store_true')
    parser.add_argument('-m', '--minimax', action='store_true')
    parser.add_argument('-s', '--self-defense', action='store_true')
    args = parser.parse_args()

    dice_count = 6
    sides = 6

    is_below = lambda s: 1 if s < 5 else 0  # noqa
    is_above = lambda s: 1 if s >= 24 else 0  # noqa
    is_win = lambda s: is_below(s) or is_above(s)  # noqa

    if args.lucky:
        below_prob = optimal_values(dice_count, sides, is_below)
        print("Probability of low success: {:.2%}".format(
                  float(below_prob[dice_count][0])))
        below_guaranteed = [[p == 1 for p in row] for row in below_prob]
        below_1st, below_1st_rolls = probability_to_reach(
            dice_count, dice_count, sides, below_guaranteed)
        print("... in first roll: {} = {:.2%}".format(
            below_1st, float(below_1st)))
        for multiplicity, outcome in below_1st_rolls:
            print("%3d * %s" %
                  (multiplicity, ''.join(str(v+1) for v in outcome)))
        above_prob = optimal_values(dice_count, sides, is_above)
        print("Probability of high success: {:.2%}".format(
                  float(above_prob[dice_count][0])))
        above_guaranteed = [[p == 1 for p in row] for row in above_prob]
        above_1st, above_1st_rolls = probability_to_reach(
            dice_count, dice_count, sides, above_guaranteed)
        print("... in first roll: {} = {:.2%}".format(
            above_1st, float(above_1st)))
        for multiplicity, outcome in above_1st_rolls:
            print("%3d * %s" %
                  (multiplicity, ''.join(str(v+1) for v in outcome)))
        return

    if args.minimax:
        print("Compute minimax strategy for %d %d-sided dice..." %
              (dice_count, sides))
        below_values = optimal_values(dice_count, sides, is_below)
        above_values = optimal_values(dice_count, sides, is_above)
        #strategy = optimizing_strategy_tiebreaks(
        #    values_max(below_values, above_values))
        utility_values = optimal_values(dice_count, sides, my_utility)
        #values = values_zip(
        #    values_max(below_values, above_values), utility_values)
        values = values_max(below_values, above_values)
        strategy = optimizing_strategy(dice_count, values)
        utility_values = compute_values(dice_count, sides, strategy, my_utility)
    elif args.self_defense:
        print("Compute self-defense strategy for %d %d-sided dice..." %
              (dice_count, sides))
        max_lose = 14
        score = lambda s: max(-max_lose, s - 24) if 5 <= s < 24 else 0
        values, strategy = solve_game(dice_count, sides, score)
        utility_values = compute_values(dice_count, sides, strategy, my_utility)
    else:
        print("Compute utility-maximizing strategy for %d %d-sided dice..." %
              (dice_count, sides))
        values, strategy = solve_game(dice_count, sides, my_utility)
        utility_values = values

    if args.describe:
        describe_strategy(dice_count, sides, values)
    elif args.infiniplay:
        v = utility_values[dice_count][0]
        print("Expected utility: %s = %.2f" % (v, float(v)))
        print("Probability of winning: {:.2%}".format(
            compute_value(dice_count, sides, strategy, is_win,
                          operator.truediv)))
        sum_utility = 0
        n_wins = 0
        n_tries = 0
        while True:
            s = play_game(dice_count, sides, strategy)
            sum_utility += my_utility(s)
            n_wins += int(is_win(s))
            n_tries += 1
            print("Utility: %s. Played %s games, " %
                  (my_utility(s), n_tries) +
                  "average utility %.2f, win rate %.2f%%" %
                  (sum_utility / n_tries, 100 * n_wins / n_tries))
    else:
        below_max_prob = roll_value_optimal(dice_count, sides, is_below)
        above_max_prob = roll_value_optimal(dice_count, sides, is_above)
        below_prob = roll_value_fixed(dice_count, sides, strategy, is_below)
        above_prob = roll_value_fixed(dice_count, sides, strategy, is_above)
        while True:
            roll = input_roll(dice_count, sides)
            min_sum = (dice_count - len(roll))
            max_sum = (dice_count - len(roll)) * sides
            roll.sort()
            roll_z = [v - 1 for v in roll]
            rerolls = [
                describe_keep_reroll(
                    dice_count, sides, strategy, roll, s)
                for s in range(min_sum, max_sum + 1)]
            if min_sum == max_sum:
                reroll, = rerolls
                print("I would %s" % reroll)
                print("If you decide to go under, your chance is at most " +
                      "{:.2%}.\n".format(
                          float(below_max_prob(roll_z))) +
                      "Otherwise, your chance is at most {:.2%}.".format(
                          float(above_max_prob(roll_z))))
            else:
                i = min_sum
                for reroll, ss in itertools.groupby(rerolls):
                    j = i + len(list(ss))
                    if i == min_sum and j == max_sum + 1:
                        print("I would %s" % reroll)
                    elif i == j - 1:
                        print("If you have %s, I would %s" % (i, reroll))
                    else:
                        print("If you have between %s and %s, I would %s" %
                              (i, j - 1, reroll))
                    i = j


if __name__ == "__main__":
    main()
