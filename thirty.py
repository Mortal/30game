import random
import argparse
import operator
import fractions
import itertools
import functools
import collections


def product(iterable):
    return functools.reduce(operator.mul, iterable, 1)


def factorial(n):
    """
    >>> [factorial(n) for n in range(6)]
    [1, 1, 2, 6, 24, 120]
    """
    return product(range(1, n+1))


def permutations(s):
    """
    >>> permutations('cat')
    6
    >>> permutations('mom')
    3
    """
    counts = collections.Counter(s)
    n = sum(counts.values())
    return factorial(n) // product(map(factorial, counts.values()))


def outcomes(sides, dice_count):
    outcomes = itertools.combinations_with_replacement(
        range(sides), dice_count)
    n_outcomes = 0
    for outcome in outcomes:
        outcome_sum = sum(outcome)
        multiplicity = permutations(outcome)
        n_outcomes += multiplicity
        yield outcome, multiplicity
    assert n_outcomes == sides ** dice_count


def compute_values_single_row(n, dice_count, sides, strategy, values,
                              div=fractions.Fraction):
    assert len(values) >= n-1
    assert n >= 1
    # What might the accumulated sum be at most with n dice remaining?
    max_sum = (dice_count - n) * (sides - 1)
    # At the end, tmp_value[s] will be k**n times the expected utility.
    tmp_value = [0 for s in range(max_sum + 1)]

    for outcome, multiplicity in outcomes(sides, n):
        for s in range(0, max_sum + 1):
            reroll = strategy(outcome, s)
            reroll_sum = sum(reroll)
            keep_sum = outcome_sum - reroll_sum
            reroll_value = values[len(reroll)][s + keep_sum]
            tmp_value[s] += multiplicity * reroll_value

    return [div(a, sides ** n) for a in tmp_value]


def compute_values(dice_count, sides, strategy, utility,
                   div=fractions.Fraction):
    # values[n][s] == v means that for n remaining dice,
    # accumulated sum s, the expected utility is v.
    values = []
    # Fill out "values" for n = 0 using the utility function.
    values.append([utility(s) for s in range(dice_count * (sides-1) + 1)])
    for n in range(1, dice_count + 1):
        values.append(compute_values_single_row(
            n, dice_count, sides, strategy, values, div=div))
    return values


def optimizing_strategy(dice_count, values):
    # What can we do with an outcome on n dice?
    # Reroll the first m (0 <= m < n) or the last m (1 <= m < n).
    rerolls = [
        [slice(0, m) for m in range(n)] +
        [slice(m, n) for m in range(1, n)]
        for n in range(dice_count + 1)]

    def reroll_strategy(outcome, current_sum=0):
        """
        "outcome" is a list of length [1, dice_count] with dice in sorted
        order. Returns the subset of the dice to reroll.
        """
        outcome_sum = sum(outcome)
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
        return outcome[best_reroll]

    return reroll_strategy


def solve_game(dice_count, sides, utility):
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
    values = []

    # Fill out "values" for n = 0 using the utility function.
    values.append([utility(s) for s in range(dice_count * (sides-1) + 1)])

    reroll_strategy = optimizing_strategy(dice_count, values)

    for n in range(1, dice_count+1):
        values.append(compute_values_single_row(
            n, dice_count, sides, reroll_strategy, values))

    return values, reroll_strategy


def value(dice_count, sides, utility):
    return solve_game(dice_count, sides, utility)[0][dice_count][0]


def compute_strategy(dice_count, sides, utility):
    return solve_game(dice_count, sides, utility)[1]


def roll_value_function(values, strategy):
    def roll_value(roll_z, current_sum=0):
        roll_sum = sum(roll_z)
        reroll = strategy(roll_z)
        reroll_sum = sum(reroll)
        keep_sum = roll_sum - reroll_sum
        return values[len(reroll)][current_sum + keep_sum]

    return roll_value


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


def describe_dice(sides, count, sum):
    if count == 1:
        return 'a %d' % (sum + 1)
    elif sum == 0:
        return '%d 1s' % count
    elif sum == count * (sides - 1):
        return '%d %ds' % (count, sides)
    elif sum == 1:
        return describe_dice(sides, count - 1, 0) + ' and a 2'
    elif sum == count * (sides - 1) - 1:
        if count == 2:
            return 'a %d and a %d' % (sides, sides - 1)
        else:
            return '%d %ds and a %d' % (count - 1, sides, sides - 1)
    else:
        return '%d dice making %d' % (count, sum + count)


def describe_choices_help(sides, n, ss):
    if len(ss) > 1 and ss == set(range(min(ss), max(ss)+1)):
        if min(ss) == 0:
            return '%d dice making at most %d' % (n, max(ss) + n)
        elif max(ss) == n * (sides - 1):
            return '%d dice making at least %d' % (n, min(ss) + n)
        else:
            return '%d dice making between %d and %d' % (
                n, min(ss) + n, max(ss) + n)
    else:
        return ' or '.join(describe_dice(sides, n, s) for s in sorted(ss))


def describe_choices(sides, dice):
    n_desc = []
    for n in set(n for n, s in dice):
        ss = set(s for n_, s in dice if n == n_)
        n_desc.append(describe_choices_help(sides, n, ss))
    return ' or '.join(n_desc)


def describe_strategy(dice_count, sides, values):
    strategy = optimizing_strategy(dice_count, values)
    is_below = lambda s: 1 if s < 5 else 0  # noqa
    is_above = lambda s: 1 if s >= 24 else 0  # noqa
    below_max_prob = compute_values(dice_count, sides, strategy, is_below)
    above_max_prob = compute_values(dice_count, sides, strategy, is_above)

    max_sum = dice_count * sides
    print(' '.join('%2d' % i for i in range(max_sum+1)))
    v_sort = sorted(set(v for row in values[0:dice_count] for v in row))
    for n, row in enumerate(values[:-1]):
        print('   '*(dice_count-n) +
              ' '.join('%02d' % v_sort.index(v)
                       for v in row))
    print("On first roll, do the first possible:")
    for v in reversed(v_sort):
        dice = [(dice_count - n, s)
                for n in range(dice_count)
                for s in range(len(values[n]))
                if values[n][s] == v]
        p = min(max(below_max_prob[dice_count - n][s],
                    above_max_prob[dice_count - n][s])
                for n, s in dice)
        print('%02d: keep %s (%.2f%%)' %
              (v_sort.index(v),
               describe_choices(sides, dice),
               float(100*p)))


def describe_keep_reroll(dice_count, sides, strategy, roll, s):
    roll_z = [v - 1 for v in roll]
    s_z = s - (dice_count - len(roll))
    reroll_z = strategy(roll_z, s_z)
    reroll = [v + 1 for v in reroll_z]

    roll_hist = collections.Counter(roll)
    reroll_hist = collections.Counter(reroll)
    keep_hist = roll_hist - reroll_hist
    keep = sorted(keep_hist.elements())
    if reroll == []:
        return 'stop'
    elif len(keep) == 1:
        return 'keep a %s' % keep[0]
    elif len(reroll) == 1:
        return 'reroll a %s' % reroll[0]
    elif len(keep) < len(reroll):
        return 'keep %s' % ' '.join(map(str, keep))
    else:
        return 'reroll %s' % ' '.join(map(str, reroll))


def roll_value_optimal(dice_count, sides, utility):
    values, strategy = solve_game(dice_count, sides, utility)
    return roll_value_function(values, strategy)


def roll_value_fixed(dice_count, sides, strategy, utility):
    values = compute_values(dice_count, sides, strategy, utility)
    return roll_value_function(values, strategy)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--infiniplay', action='store_true')
    parser.add_argument('-d', '--describe', action='store_true')
    args = parser.parse_args()

    dice_count = 6
    sides = 6
    print("Compute optimal strategy for %d %d-sided dice..." %
          (dice_count, sides))
    values, strategy = solve_game(dice_count, sides, my_utility)

    if args.describe:
        describe_strategy(dice_count, sides, values)
    elif args.infiniplay:
        v = values[dice_count][0]
        print("Expected utility: %s = %.2f" % (v, float(v)))
        sum_utility = 0
        n_tries = 0
        while True:
            s = play_game(dice_count, sides, strategy)
            sum_utility += my_utility(s)
            n_tries += 1
            print("Utility: %s. Played %s games, average utility %.2f" %
                  (my_utility(s), n_tries, sum_utility / n_tries))
    else:
        is_below = lambda s: 1 if s < 5 else 0  # noqa
        is_above = lambda s: 1 if s >= 24 else 0  # noqa
        below_max_prob = roll_value_optimal(dice_count, sides, is_below)
        above_max_prob = roll_value_optimal(dice_count, sides, is_above)
        below_prob = roll_value_fixed(dice_count, sides, strategy, is_below)
        above_prob = roll_value_fixed(dice_count, sides, strategy, is_above)
        while True:
            try:
                roll_str = input('Input your roll: ')
            except (KeyboardInterrupt, EOFError):
                print('')
                break
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
                          float(below_max_prob(roll_z)),
                          float(below_prob(roll_z))) +
                      "Otherwise, your chance is at most {:.2%}.".format(
                          float(above_max_prob(roll_z)),
                          float(above_prob(roll_z))))
            else:
                i = min_sum
                for reroll, ss in itertools.groupby(rerolls):
                    j = i + len(list(ss))
                    print("If you have between %s and %s, I would %s" %
                          (i, j - 1, reroll))
                    i = j


if __name__ == "__main__":
    main()
