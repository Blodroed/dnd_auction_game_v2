from typing import List
from itertools import product


def dice_score(num: int, die: int, bonus: int) -> List[int]:
    """
    Returns a sorted list of all possible outcomes for rolling 'num' dice of 'die' sides, plus 'bonus'.
    The length of the list will be num (number of dice), but each entry is the sum for that outcome.

    Arguments:
        num: number of dice to roll
        die: type of die (e.g., 6 for d6)
        bonus: flat bonus to add to the roll
    """

    # Generate all possible rolls
    rolls = product(range(1, die + 1), repeat=num)
    outcomes = sorted(set(sum(roll) + bonus for roll in rolls))
    return outcomes

def average_roll(num: int, die: int, bonus: int) -> float:
    """
    Returns the average outcome for rolling 'num' dice of 'die' sides, plus 'bonus'.

    Arguments:
        num: number of dice to roll
        die: type of die (e.g., 6 for d6)
        bonus: flat bonus to add to the roll
    """
    mean_die = (die + 1) / 2
    return num * mean_die + bonus

def average_roll_for_die(die: int) -> float:
    """
    Returns the average outcome for rolling a single die of 'die' sides.

    Arguments:
        die: type of die (e.g., 6 for d6)
    """
    return (die + 1) / 2

def fast_dice_stats(num: int, die: int, bonus: int) -> dict:
    """
    Returns a dictionary with min, max, mean, and median outcomes for rolling 'num' dice of 'die' sides, plus 'bonus'.

    Arguments:
        num: number of dice to roll
        die: type of die (e.g., 6 for d6)
        bonus: flat bonus to add to the roll
    """
    outcomes = dice_score(num, die, bonus)
    n = len(outcomes)
    mean = sum(outcomes) / n
    median = outcomes[n // 2] if n % 2 == 1 else (outcomes[n // 2 - 1] + outcomes[n // 2]) / 2

    return {
        "min": outcomes[0],
        "max": outcomes[-1],
        "mean": mean,
        "median": median
    }
