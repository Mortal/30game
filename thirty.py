import random
import argparse
import operator
import itertools
import collections
from rolls import (
    combinations_summing_to, outcomes_summing_to, subsequences,
)
from policyeval import (
    probability_to_reach, compute_values, compute_value, optimizing_strategy,
    values_max, solve_game, optimal_values, roll_value_function,
)


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
    #elif sum == count * (sides - 1) - 1:
    #    if count == 2:
    #        return 'a %d and a %d' % (sides, sides - 1)
    #    else:
    #        return '%d %ds and a %d' % (count - 1, sides, sides - 1)
    else:
        return '%d dice making %d' % (count, sum + count)


def describe_choices_help(sides, n, ss):
    if n == 1:
        a_ss = ['a %s' % (s+n) for s in sorted(ss)]
        if len(ss) == 1:
            return a_ss[0]
        else:
            return '%s or %s' % (', '.join(a_ss[:-1]), a_ss[-1])
    start = {min(ss)} | {s for s in ss if s - 1 not in ss}
    stop = {max(ss)} | {s for s in ss if s + 1 not in ss}
    descs = []
    for a, b in zip(sorted(start), sorted(stop)):
        if a == b:
            descs.append(describe_dice(sides, n, a))
        elif a == 0:
            descs.append('%d dice making at most %d' % (n, b + n))
        elif b == n * (sides - 1):
            descs.append('%d dice making at least %d' % (n, a + n))
        else:
            descs.append('%d dice making between %d and %d' %
                         (n, a + n, b + n))
    return ' or '.join(descs)


def describe_choices(sides, dice):
    n_desc = []
    for n in set(n for n, s in dice):
        ss = set(s for n_, s in dice if n == n_)
        n_desc.append(describe_choices_help(sides, n, ss))
    return ' or '.join(n_desc)


def can_cooccur(sides, dice, n1, s1, n2, s2):
    """
    Returns True if there exists outcomes where there is a choice between
    (n1, s1) and (n2, s2).

    >>> can_cooccur(6, 6, 5, 0, 4, 0)
    True
    >>> can_cooccur(6, 6, 5, 25, 4, 0)
    False
    >>> can_cooccur(6, 6, 6, 27, 3, 0)
    False
    """
    if n1 == n2 == dice:
        return s1 == s2
    max1 = s1 + (dice - n1) * (sides - 1)
    max2 = s2 + (dice - n2) * (sides - 1)
    return s1 <= max2 and s2 <= max1


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
    seen = set()
    actions = []
    for v in reversed(v_sort):
        rerolls = [(n, s)
                   for n in range(dice_count)
                   for s in range(len(values[n]))
                   if values[n][s] == v]
        all_dice = [(dice_count - n, s) for n, s in rerolls]
        dice = []
        for n, s in all_dice:
            # Have all the possible ways of rolling n dice making s
            # already been covered by the strategy?
            all_seen_before = all(
                any((len(ss), sum(ss)) in seen
                    for ss in subsequences(outcome))
                for outcome in combinations_summing_to(sides, n, s))
            if not all_seen_before:
                seen.add((n, s))
                dice.append((n, s))
        if dice:
            actions.append(dice)

    unconditional_action = []
    conditional_actions = []
    for i, dice in enumerate(actions):
        a = []
        for n, s in dice:
            outcomes = outcomes_summing_to(sides, dice_count, n, s)
            if any(can_cooccur(sides, dice_count, n, s, n_, s_)
                   for j in range(i) for n_, s_ in actions[j]):
                a.append((n, s))
            else:
                unconditional_action.append((n, s))
        if a:
            conditional_actions.append(a)
    for i in range(len(conditional_actions)):
        if len(conditional_actions[i]) > 1:
            continue
        (n, s), = conditional_actions[i]
        for j in range(i, 0, -1):
            if len(conditional_actions[j-1]) > 1:
                break
            (n2, s2), = conditional_actions[j-1]
            if n < n2 or can_cooccur(sides, dice_count, n, s, n2, s2):
                break
            conditional_actions[j-1], conditional_actions[j] = (
                conditional_actions[j], conditional_actions[j-1])
    actions = [unconditional_action] + conditional_actions

    print("On first roll, do the first possible:")
    for i, dice in enumerate(actions):
        p_win = min(max(below_max_prob[dice_count - n][s],
                        above_max_prob[dice_count - n][s])
                    for n, s in dice)
        n_outcomes = 0
        for n, s in dice:
            outcomes = outcomes_summing_to(sides, dice_count, n, s)
            for outcome, multiplicity in outcomes:
                n_outcomes += multiplicity
        print('keep %s (%.2f%%, %s)' %
              (describe_choices(sides, dice),
               float(100*p_win), n_outcomes))


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
