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


def value(dice_count, sides, utility, full=False):
    """
    Suppose we have n k-sided dice (sides 0, 1, ..., k-1)
    and we perform the following process:
    Throw the dice, and take out a non-empty subset of them,
    remembering the sum.  As long as you still have dice left, throw the
    remaining dice, and take out a non-empty subset of them, adding up their
    sum with what you already put aside.
    When you have no more dice, you have a resulting sum (between 0 and n*(k-1))
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

    # How do you divide two numbers?
    div = fractions.Fraction

    # What can we do with an outcome on n dice?
    # Reroll the first m (0 <= m < n) or the last m (1 <= m < n).
    rerolls = [
        [slice(0, m) for m in range(n)] +
        [slice(m, n) for m in range(1, n)]
        for n in range(dice_count + 1)]

    def reroll_strategy(outcome, s=0):
        """
        "outcome" is a list of length [1, dice_count] with die faces in sorted
        order. Returns (reroll, value) where "reroll" is a subset of the dice
        and "value" is the expected utility.
        """
        outcome_sum = sum(outcome)
        best_reroll = best = None
        for reroll_slice in rerolls[len(outcome)]:
            reroll = outcome[reroll_slice]
            reroll_sum = sum(reroll)
            keep_sum = outcome_sum - reroll_sum
            # Suppose we had already accumulated "s",
            # and now we keep another "keep_sum"
            # and reroll the "reroll" dice.
            v = values[len(reroll)][s + keep_sum]
            if best_reroll is None or best < v:
                best_reroll = reroll
                best = v
        return best_reroll, best

    for n in range(1, dice_count+1):
        # What might the accumulated sum be at most with n dice remaining?
        max_sum = (dice_count - n) * (sides - 1)
        # At the end, tmp_value[s] will be k**n times the expected utility.
        tmp_value = [0 for s in range(max_sum + 1)]

        outcomes = itertools.combinations_with_replacement(range(sides), n)
        n_outcomes = 0
        for outcome in outcomes:
            multiplicity = permutations(outcome)
            n_outcomes += multiplicity
            for s in range(0, max_sum + 1):
                reroll, reroll_value = reroll_strategy(outcome, s)
                tmp_value[s] += multiplicity * reroll_value

        assert n_outcomes == sides ** n

        values.append([div(a, n_outcomes) for a in tmp_value])

    if full:
        return values[dice_count][0], reroll_strategy
    else:
        return values[dice_count][0]


def play_game(dice_count, sides, strategy):
    outcome = sorted(random.randrange(sides) for _ in range(dice_count))
    s = 0
    while outcome:
        print("Sum: %2d  You roll: %s -> %s" %
              (s + dice_count - len(outcome),
               [a + 1 for a in outcome],
               s + dice_count + sum(outcome)))
        reroll, value = strategy(outcome, s)
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
    lose = -1
    strictly_below = 20
    dead_on = 6
    above = [2, 4, 8, 14, 20, 30]

    # "Skarpt under 11" => strictly less than 5
    # "30" => 24
    if s < 5:
        return strictly_below
    elif s < 24:
        # return 24 - s
        return lose * (24 - s)
    elif s == 24:
        return dead_on
    else:
        return above[s - 25]


def describe_keep_reroll(dice_count, sides, strategy, roll, s):
    roll_z = [v - 1 for v in roll]
    s_z = s - (dice_count - len(roll))
    reroll_z = strategy(roll_z, s_z)[0]
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--infiniplay', action='store_true')
    args = parser.parse_args()

    dice_count = 6
    sides = 6
    v, strategy = value(dice_count, sides, my_utility, True)

    if args.infiniplay:
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
        below_strategy = value(
            dice_count, sides, (lambda s: 1 if s < 5 else 0), True)[1]
        above_strategy = value(
            dice_count, sides, (lambda s: 1 if s >= 24 else 0), True)[1]
        while True:
            try:
                roll_str = input('Input your roll: ')
            except KeyboardInterrupt:
                print('')
                break
            try:
                roll = [int(v) for v in roll_str.split()]
            except ValueError:
                print("Hmm, try again.")
                continue
            if len(roll) > dice_count:
                print("You can only roll %s dice at a time!" % dice_count)
                continue
            if not all(1 <= v <= sides for v in roll):
                print("Those are not the %s-sided dice I know!" % sides)
            min_sum = (dice_count - len(roll))
            max_sum = (dice_count - len(roll)) * sides
            roll.sort()
            roll_z = [v - 1 for v in roll]
            rerolls = [
                strategy(roll_z, s - min_sum)[0]
                for s in range(min_sum, max_sum + 1)]
            if min_sum == max_sum:
                reroll, = rerolls
                print("I would reroll %s" %
                      ([v + 1 for v in reroll] or 'nothing'))
                _, below_prob = below_strategy(roll_z)
                _, above_prob = above_strategy(roll_z)
                print(("If you decide to go under, your chance is {:.2%}.\n" +
                       "Otherwise, your chance is {:.2%}.").format(
                           float(below_prob), float(above_prob)))
            else:
                i = min_sum
                for reroll, ss in itertools.groupby(rerolls):
                    j = i + len(list(ss))
                    print("If you have between %s and %s, I would reroll %s" %
                          (i, j - 1, [v + 1 for v in reroll] or 'nothing'))
                    i = j


if __name__ == "__main__":
    main()
