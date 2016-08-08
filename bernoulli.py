import operator
import fractions
import functools


def product(iterable):
    return functools.reduce(operator.mul, iterable, 1)


def factorial(n):
    """
    >>> [factorial(n) for n in range(6)]
    [1, 1, 2, 6, 24, 120]
    """
    return product(range(1, n+1))


def main():
    dice_count = 6
    sides = 6
    p = fractions.Fraction(1, sides)

    no_success = (1 - p) ** dice_count
    print("Pr[no successes in first try] = %s\n= %.2f" %
          (no_success, float(no_success)))

    count = [0]
    all_prob = [1]
    for n in range(1, dice_count+1):
        # Suppose we have n dice left.
        # Each outcome corresponds to a number of successes.
        t_count = 0
        t_all_prob = 0
        prob_sum = 0
        for outcome in range(0, n+1):
            # "outcome" successes.
            outcome_multiplicity = (
                factorial(n) //
                (factorial(outcome) * factorial(n - outcome)))
            outcome_prob = (
                outcome_multiplicity *
                p ** outcome *
                (1 - p) ** (n - outcome))
            if outcome == 0:
                # It ends now.
                t_all_prob += 0 * outcome_prob
                t_count += 0 * outcome_prob
            else:
                t_all_prob += all_prob[n - outcome] * outcome_prob
                t_count += (outcome + count[n - outcome]) * outcome_prob
            prob_sum += outcome_prob
        assert prob_sum == 1, (n, prob_sum)
        print("E[#successes with %d dice] = %s" % (n, t_count))
        print("Pr[all %d dice succeed] = %s" % (n, t_all_prob))
        count.append(t_count)
        all_prob.append(t_all_prob)
    # W.p. all_prob[-1], we start over (add "dice_count" to success);
    # w.p. 1-all_prob[-1], we don't (with exp. success count[-1]).
    # Thus total number of successes X is
    # X = all_prob[-1] * (dice_count + X) + (1-all_prob[-1]) * count[-1].
    # X * (1 - all_prob[-1]) = dice_count * all_prob[-1] +
    #                          (1-all_prob[-1]) * count[-1].
    X = (dice_count * all_prob[-1] +
         (1-all_prob[-1]) * count[-1]) / (1 - all_prob[-1])
    print("E[#successes with %d dice and startovers] =\n%s\n= %.2f" %
          (dice_count, X, float(X)))


if __name__ == "__main__":
    main()
