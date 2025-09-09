"""
Collection of strategy functions for deciding player actions in Blackjack.

Each strategy is a callable accepting the current player hand and the
dealer's upcard (rank only) and returning one of the strings ``"hit"``,
``"stand"``, ``"double"``, or ``"split"``.  Not all strategies support
splitting or doubling; they should avoid returning those actions when not
permitted.

Strategies included:

* ``simplest`` – Hits until 17 or more, then stands.
* ``random`` – Chooses between hit and stand at random.
* ``basic`` – Implements a simplified version of the Basic Strategy,
  including splitting and doubling rules.

The strategies are exported in the ``STRATEGIES`` dictionary for easy
lookup.
"""

from typing import Dict
from game import HandState, VALUES


def simplest_strategy(hand: HandState, dealer_up: str) -> str:
    """Always hit below 17, else stand."""
    return "hit" if hand.value < 17 else "stand"


def random_strategy(hand: HandState, dealer_up: str) -> str:
    """Randomly choose between hit and stand."""
    import random
    return random.choice(["hit", "stand"])


def basic_strategy(hand: HandState, dealer_up: str) -> str:
    """
    Simplified Basic Strategy covering splits, soft totals, and hard totals.
    Adapted to a single‐deck perspective and to ranks without suits.

    :param hand: The player's current hand state.
    :param dealer_up: Dealer's upcard rank.
    :returns: One of 'hit', 'stand', 'double', or 'split'.
    """
    dealer_val = VALUES[dealer_up]

    # Check for split opportunities first
    if hand.can_split():
        rank = hand.cards[0]
        # Pairs by rank (using rank strings)
        if rank == "A":
            return "split"
        if rank == "10":
            return "stand"
        if rank == "9":
            return "split" if (2 <= dealer_val <= 9 and dealer_val != 7) else "stand"
        if rank == "8":
            return "split"
        if rank == "7":
            return "split" if 2 <= dealer_val <= 7 else "hit"
        if rank == "6":
            return "split" if 2 <= dealer_val <= 6 else "hit"
        if rank == "5":
            return "double" if (2 <= dealer_val <= 9 and hand.can_double()) else "hit"
        if rank == "4":
            return "split" if 5 <= dealer_val <= 6 else "hit"
        if rank in ("3", "2"):
            return "split" if 2 <= dealer_val <= 7 else "hit"

    # Determine if the hand is soft (counting an Ace as 11)
    # A hand is soft if it contains at least one Ace that could be counted as 11
    total = 0
    aces = 0
    for c in hand.cards:
        if c == "A":
            total += 11
            aces += 1
        else:
            total += VALUES[c]
    # reduce soft Aces until total is <=21
    while total > 21 and aces > 0:
        total -= 10
        aces -= 1
    is_soft = aces > 0 and total == hand.value and hand.value <= 21

    # Soft totals decisions
    if is_soft:
        if hand.value == 20:  # A,9
            return "stand"
        if hand.value == 19:  # A,8
            return "double" if dealer_val == 6 and hand.can_double() else "stand"
        if hand.value == 18:
            if 2 <= dealer_val <= 6 and hand.can_double():
                return "double"
            if 9 <= dealer_val <= 11:
                return "hit"
            return "stand"
        if hand.value == 17:
            return "double" if 3 <= dealer_val <= 6 and hand.can_double() else "hit"
        if hand.value in (15, 16):
            return "double" if 4 <= dealer_val <= 6 and hand.can_double() else "hit"
        if hand.value in (13, 14):
            return "double" if 5 <= dealer_val <= 6 and hand.can_double() else "hit"

    # Hard totals
    if hand.value >= 17:
        return "stand"
    if 13 <= hand.value <= 16:
        return "stand" if dealer_val < 7 else "hit"
    if hand.value == 12:
        return "stand" if 4 <= dealer_val <= 6 else "hit"
    if hand.value == 11:
        return "double" if hand.can_double() else "hit"
    if hand.value == 10:
        return "double" if dealer_val <= 9 and hand.can_double() else "hit"
    if hand.value == 9:
        return "double" if 3 <= dealer_val <= 6 and hand.can_double() else "hit"
    return "hit"


STRATEGIES: Dict[str, callable] = {
    "simplest": simplest_strategy,
    "random": random_strategy,
    "basic": basic_strategy,
}