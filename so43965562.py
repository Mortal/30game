# exec "g/^\\S/d"|%<|exec "w !python"|u

The solution you post will probably never finish, since it would require going through more than 10^21 combinations of elements. Rather than using multiprocessing you should use a faster algorithm.

Using the list1, list2 and lists_out
that you use in your question, we are looking for ways to combine integers between
16 and 36 so that they sum to the lengths of the sequences in list1 and list2.
The combinations should be of 7 or 8 integers in the range [16, 36].

    import itertools
    def so43965562(list1, list2, lists_out, lower=16, upper=36):
        assert len(list1) == len(list2) == len(lists_out)
        for n in (7, 8):
            for i in range(len(list1)):
                # Find all combinations of n numbers in [lower, upper]
                # that sum to len(list1[i])
                combs1 = combinations_summing_to(lower, upper, n, len(list1[i]))
                # Find all combinations of n numbers in [lower, upper]
                # that sum to len(list2[i])
                combs2 = combinations_summing_to(lower, upper, n, len(list2[i]))
                for t1, t2 in itertools.product(combs1, combs2):
                    result = [(v1, v2) for v1, v2 in zip(t1, t2)]
                    lists_out[i].append(result)

The following function writes `s` as a sum of `n` integers between `l` and `u`.

    def combinations_summing_to(l, u, n, s, suffix=()):
        """In which ways can s be written as the sum of n integers in [l, u]?

        >>> # Write 2 as a sum of 4 integers between 0 and 5.
        >>> print(list(combinations_summing_to(0, 5, 4, 2)))
        [(0, 0, 0, 2), (0, 0, 1, 1)]
        >>> # Write 5 as a sum of 3 integers between 0 and 5.
        >>> print(list(combinations_summing_to(0, 5, 3, 5)))
        [(0, 0, 5), (0, 1, 4), (0, 2, 3), (1, 1, 3), (1, 2, 2)]
        >>> # Write 5 as a sum of 3 integers between 0 and 5.
        >>> print(list(combinations_summing_to(0, 5, 3, 12)))
        [(2, 5, 5), (3, 4, 5), (4, 4, 4)]
        >>> # Write 34 as a sum of 2 integers between 16 and 36.
        >>> print(list(combinations_summing_to(16, 36, 2, 34)))
        [(16, 18), (17, 17)]
        """
        if n == 0:
            return (suffix,) if s == 0 else ()
        elif n == 1:
            return ((s,) + suffix,) if l <= s <= u else ()
        else:
            return itertools.chain.from_iterable(
                # Combinations summing to s where the last element is k
                combinations_summing_to(l, k, n - 1, s - k, (k,) + suffix)
                for k in range(u, l-1, -1)
                # Early bailout if you can't make s with all elements <= k
                if l * n <= s <= k * n)

You can run the solution as follows:

    lists_out = [[]]
    so43965562(list1=[[0]*(7*16+1)], list2=[[0]*(7*16+2)], lists_out=lists_out)
    for result in lists_out[0]:
        print(result)
    # Outputs the following two combinations:
    # [(16, 16), (16, 16), (16, 16), (16, 16), (16, 16), (16, 16), (17, 18)]
    # [(16, 16), (16, 16), (16, 16), (16, 16), (16, 16), (16, 17), (17, 17)]
    lists_out = [[]]
    n = 133
    so43965562(list1=[[0]*n], list2=[[0]*n], lists_out=lists_out)
    print(len(lists_out[0]))
    # Outputs 1795769, takes about 2.5 seconds to run.

Note that the output size increases exponentially, starting at
nothing when n = 7*16 = 112, so it will still take a long time to compute
all the combinations when n = 198 as you write in your question.
