import collections
from rolls import (
    combinations_summing_to, outcomes_summing_to, subsequences,
)
from policyeval import compute_values, optimizing_strategy


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
