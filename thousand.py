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


def permutations_counter(counts):
    n = sum(counts.values())
    return factorial(n) // product(map(factorial, counts.values()))


def permutations(s):
    """
    >>> permutations('cat')
    6
    >>> permutations('mom')
    3
    """
    return permutations_counter(collections.Counter(s))


def outcomes(sides, dice_count):
    outcomes = itertools.combinations_with_replacement(
        range(sides), dice_count)
    n_outcomes = 0
    n_distinct = 0
    for outcome in outcomes:
        multiplicity = permutations(outcome)
        n_outcomes += multiplicity
        n_distinct += 1
        yield outcome, multiplicity
    assert n_outcomes == sides ** dice_count
    assert n_distinct == (factorial(dice_count + sides-1) //
                          (factorial(dice_count) * factorial(sides-1)))


def outcomes_counter(sides, dice_count):
    return ((collections.Counter(outcome), multiplicity)
            for outcome, multiplicity in outcomes(sides, dice_count))


def actions(counter):
    """
    >>> sorted(actions({0: 2, 3: 2, 5: 2}))
    [(0, 20), (4, 4), (5, 2)]
    >>> sorted(actions({0: 4}))
    [(0, 40), (1, 20), (2, 4), (3, 2)]
    """
    dice_count = sum(counter.values())

    # If n is in keep_counts[i], then we may keep n of keep_keys[i].
    keep_keys = []
    keep_counts = []
    for k, v in counter.items():
        if k in (0, 4):
            # We may keep any number of these.
            keep_keys.append(k)
            keep_counts.append(list(range(v+1)))
        elif v >= 3:
            # We may keep at least three of these.
            keep_keys.append(k)
            keep_counts.append([0] + list(range(3, v+1)))

    pairs = sum(1 for k in counter if counter[k] >= 2)
    if pairs >= 3:
        # 3 pairs -- take all dice
        yield (0, 1000 // 50)
    if len(counter) >= 6:
        # 6 distinct -- take all dice
        yield (0, 1500 // 50)
    for counts in itertools.product(*keep_counts):
        if not any(counts):
            # We can't take no dice.
            continue
        score = 0
        for k, c in zip(keep_keys, counts):
            if c >= 3:
                if k == 0:
                    score += 1000 // 50 * (c - 2)
                else:
                    score += (k+1) * 100 // 50 * (c - 2)
            elif k == 0:
                score += 100 // 50 * c
            elif k == 4:
                score += 50 // 50 * c
        yield (dice_count - sum(counts), score)


def can_keep_points(starting_score, current_score):
    if starting_score == 0 and current_score <= 1000 // 50:
        return False
    if starting_score >= 9000 // 50 and current_score + starting_score < 10000 // 50:
        return False
    return True


def compute_values_single(dice_count, sides, remaining_dice,
                          starting_score, current_score, strategy, values,
                          div=fractions.Fraction):
    assert remaining_dice >= 1
    # At the end, tmp_value will be k**n times the expected utility.
    tmp_value = 0

    for counter, multiplicity in outcomes_counter(sides, remaining_dice):
        a = list(actions(counter))
        assert all(s > 0 for r, s in a)
        if a:
            action_index, do_continue = strategy(
                counter, starting_score, current_score, a)
            reroll_dice, keep_score = a[action_index]
            if do_continue:
                result = values.play(
                    reroll_dice or dice_count, starting_score,
                    current_score + keep_score)
            else:
                result = values.stop(
                    starting_score, current_score + keep_score)
        else:
            result = values.nothing(starting_score)
        tmp_value += multiplicity * result

    return div(tmp_value, sides ** remaining_dice)


def ensure_numeric(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        v = f(*args, **kwargs)
        if isinstance(v, bool):
            return int(v)
        else:
            return v

    return wrapper


class Values(object):
    def __init__(self, dice_count, utility):
        max_score = 10000 // 50
        self._values = [[[None for c in range(max_score - s + 1)]
                         for s in range(max_score + 1)]
                        for r in range(dice_count)]
        self._utility = [utility(s) for s in range(max_score + 1)]

    def play(self, remaining_dice, starting_score, current_score):
        max_score = 10000 // 50
        if starting_score + current_score >= max_score:
            return self.utility(max_score)
        current_score = min(current_score, max_score - starting_score)
        v = self._values[remaining_dice-1][starting_score][current_score]
        if v is None:
            print("Try to evaluate (%s, %s, %s)" % (starting_score, current_score, remaining_dice))
        assert v is not None
        return v

    def set_value(self, remaining_dice, starting_score, current_score, v):
        max_score = 10000 // 50
        assert starting_score <= max_score
        assert current_score <= max_score - starting_score
        self._values[remaining_dice-1][starting_score][current_score] = v

    def stop(self, starting_score, current_score):
        if can_keep_points(starting_score, current_score):
            return self.utility(starting_score + current_score)
        else:
            return self.utility(starting_score)

    def nothing(self, starting_score):
        return self.utility(starting_score)

    def utility(self, score):
        if score > 10000 // 50:
            return self._utility[10000 // 50]
        else:
            return self._utility[score]


def fill_out_values(dice_count, sides, strategy, values,
                    div=fractions.Fraction):
    max_score = 10000 // 50
    for starting_score in range(max_score, -1, -1):
        print("Fill out %s" % starting_score, flush=True)
        for current_score in range(max_score - starting_score, -1, -1):
            for remaining_dice in range(1, dice_count + 1):
                values.set_value(
                    remaining_dice, starting_score, current_score,
                    compute_values_single(
                        dice_count, sides, remaining_dice, starting_score,
                        current_score, strategy, values, div=div))
    return values


def compute_values(dice_count, sides, strategy, utility,
                   div=fractions.Fraction):
    utility = ensure_numeric(utility)
    values = Values(dice_count, utility)
    fill_out_values(dice_count, sides, strategy, values, div=div)
    return values


def compute_value(dice_count, sides, strategy, utility,
                  div=fractions.Fraction):
    values = compute_values(dice_count, sides, strategy, utility, div=div)
    return values.play(dice_count, 0, 0)


def optimizing_strategy(dice_count, values):
    def reroll_strategy(counter, starting_score, current_score, actions):
        """
        "counter" is a Counter with the outcome,
        "starting_score"/"current_score" is the current state, and "actions"
        is a list of possible actions (list of (reroll dice, add score)).
        Returns (i, c) where actions[i] is the action chosen by the strategy
        and c is True if we want to continue rolling.
        """
        best_reroll = best_continue = best_value = None
        for i, (reroll_dice, add_score) in enumerate(actions):
            # print(reroll_dice, add_score)
            assert add_score > 0
            continue_score = values.play(
                reroll_dice or dice_count,
                starting_score, current_score + add_score)
            stop_score = values.stop(
                starting_score, current_score + add_score)
            if best_reroll is None or best_value < continue_score:
                best_reroll = i
                best_continue = True
                best_value = continue_score
            if reroll_dice and best_reroll is None or best_value < stop_score:
                best_reroll = i
                best_continue = False
                best_value = stop_score
        return best_reroll, best_continue

    return reroll_strategy


def random_strategy(counter, starting_score, current_score, actions):
    i = random.choice(range(len(actions)))
    reroll_dice, add_score = actions[i]
    if reroll_dice:
        do_continue = random.choice([False, True])
    else:
        do_continue = True
    return i, do_continue


def max_strategy(counter, starting_score, current_score, actions):
    i = max(range(len(actions)), key=lambda i: actions[i][1])
    reroll_dice, add_score = actions[i]
    if reroll_dice:
        if can_keep_points(starting_score, current_score + add_score):
            do_continue = False
        else:
            do_continue = True
    else:
        do_continue = True
    return i, do_continue


def solve_game(dice_count, sides, utility, div=fractions.Fraction):
    utility = ensure_numeric(utility)
    values = Values(dice_count, utility)
    strategy = optimizing_strategy(dice_count, values)
    fill_out_values(dice_count, sides, strategy, values, div=div)
    return values, strategy


def value(dice_count, sides, utility):
    return solve_game(dice_count, sides, utility)[0].play(dice_count, 0, 0)


def optimal_values(dice_count, sides, utility):
    return solve_game(dice_count, sides, utility)[0]


def compute_strategy(dice_count, sides, utility):
    return solve_game(dice_count, sides, utility)[1]


def play_game(dice_count, sides, strategy):
    reroll_dice = dice_count
    starting_score = current_score = 0
    while starting_score < 10000 // 50:
        counter = collections.Counter(
            [random.randrange(sides) for _ in range(reroll_dice)])
        print("Starting score: %4d  Current score: %4d  You roll: %s" %
              (50 * starting_score, 50 * current_score,
               sorted(a + 1 for a in counter.elements())))
        a = list(actions(counter))
        if not a:
            print("Too bad!")
            break
        action_index, do_continue = strategy(
            counter, starting_score, current_score, a)
        reroll_dice, keep_score = a[action_index]
        if not reroll_dice and not do_continue:
            print("You can't stop with 0 dice, cheater!")
            raise Exception("Cheater")
        current_score += keep_score
        if do_continue:
            reroll_dice = reroll_dice or dice_count
            print("You reroll %s dice" % reroll_dice)
        else:
            starting_score, current_score = starting_score + current_score, 0
            print("Next turn")
            reroll_dice = dice_count
    return starting_score


def my_utility(score):
    return int(score >= 10000 // 50)


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
    parser.add_argument('-r', '--random', action='store_true')
    parser.add_argument('-m', '--max', action='store_true')
    args = parser.parse_args()

    dice_count = 6
    sides = 6

    if args.max:
        strategy = max_strategy
        expected_utility = 0
    elif args.random:
        strategy = random_strategy
        expected_utility = 0
    else:
        print("Compute utility-maximizing strategy for %d %d-sided dice..." %
              (dice_count, sides))
        values, strategy = solve_game(dice_count, sides, my_utility)
        expected_utility = values.play(dice_count, 0, 0)

    is_win = lambda score: score >= 10000 // 50

    if args.infiniplay:
        v = expected_utility
        print("Expected utility: %s = %.2f" % (v, float(v)))
        # print("Probability of winning: {:.2%}".format(
        #     compute_value(dice_count, sides, strategy, is_win,
        #                   operator.truediv)))
        sum_utility = 0
        n_wins = 0
        n_tries = 0
        while True:
            s = play_game(dice_count, sides, strategy)
            sum_utility += my_utility(s)
            n_wins += int(is_win(s))
            n_tries += 1
            print("Utility: %s. Won %s out of %s games, " %
                  (my_utility(s), n_wins, n_tries) +
                  "average utility %.2f, win rate %.2f%%" %
                  (sum_utility / n_tries, 100 * n_wins / n_tries))


if __name__ == "__main__":
    main()
