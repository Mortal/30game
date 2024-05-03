import collections
from typing import Sequence

from policyeval import Strategy


def describe_keep_reroll(
    dice_count: int, sides: int, strategy: Strategy, roll: Sequence[int], s: int
) -> str:
    roll_z = [v - 1 for v in roll]
    s_z = s - (dice_count - len(roll))
    reroll_z = strategy(roll_z, s_z)
    reroll = [v + 1 for v in reroll_z]

    roll_hist = collections.Counter(roll)
    reroll_hist = collections.Counter(reroll)
    keep_hist = roll_hist - reroll_hist
    keep = sorted(keep_hist.elements())
    if reroll == []:
        return "stop"
    elif len(keep) == 1:
        return "keep a %s" % keep[0]
    elif len(reroll) == 1:
        return "reroll a %s" % reroll[0]
    elif len(keep) < len(reroll):
        return "keep %s" % " ".join(map(str, keep))
    else:
        return "reroll %s" % " ".join(map(str, reroll))
