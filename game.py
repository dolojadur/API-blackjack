"""
Core game logic for simulating rounds of Blackjack without suits and with
Hi‑Lo counting.

This module defines the classes and functions necessary to model a shoe,
hands, and the flow of a Blackjack round.  Card ranks are tracked without
their suits; each deck contributes four copies of each rank into the shoe.
The probability of drawing each rank therefore diminishes appropriately
when a particular rank is dealt.

The simulation supports basic game actions: hit, stand, double, and split.
It updates the running Hi‑Lo count after each round and provides the true
count used to adjust bets for subsequent rounds.
"""

from dataclasses import dataclass
from typing import Callable, List, Optional
import random


# ----- Card definitions -----
RANKS: List[str] = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
VALUES = {
    "A": 11,
    "2": 2,
    "3": 3,
    "4": 4,
    "5": 5,
    "6": 6,
    "7": 7,
    "8": 8,
    "9": 9,
    "10": 10,
    "J": 10,
    "Q": 10,
    "K": 10,
}


def hi_lo_value(rank: str) -> int:
    """Return the Hi‑Lo count value for a given rank."""
    if rank in ("2", "3", "4", "5", "6"):
        return 1
    if rank in ("7", "8", "9"):
        return 0
    return -1  # 10, J, Q, K, A


class Shoe:
    """
    A shoe containing multiple decks of 52 cards, but only storing card
    ranks (suits are omitted).  Each rank appears four times per deck.

    The shoe reshuffles automatically when 75%% of its cards have been
    dealt (i.e. when only 25%% remain), resetting the running Hi‑Lo count.
    """

    def __init__(self, num_decks: int = 6, shuffle_seed: Optional[int] = None) -> None:
        self.num_decks = num_decks
        self._rng = random.Random(shuffle_seed)
        self._cards_total = 0
        self._shoe: List[str] = []
        self.reshuffle()

    def reshuffle(self) -> None:
        """Reshuffle the shoe by loading all decks and randomising the order."""
        self._shoe = []
        for _ in range(self.num_decks):
            for rank in RANKS:
                # 4 copies per rank per deck
                self._shoe.extend([rank] * 4)
        self._rng.shuffle(self._shoe)
        self._cards_total = len(self._shoe)

    def cards_remaining(self) -> int:
        return len(self._shoe)

    def decks_remaining(self) -> float:
        return max(0.0001, len(self._shoe) / 52.0)

    def pop(self) -> str:
        """
        Pop one card rank from the shoe.  If fewer than 25%% of cards remain,
        the shoe is automatically reshuffled.
        
        if len(self._shoe) <= 0.25 * self._cards_total:
            self.reshuffle()
        """
        return self._shoe.pop()


@dataclass
class HandState:
    """Represents a player's or dealer's hand and the associated bet."""

    cards: List[str]
    bet: float
    actions: List[str]
    doubled: bool = False

    @property
    def value(self) -> int:
        """
        Compute the Blackjack value of the hand, counting Aces as 1 or 11
        to avoid busting where possible.
        """
        total = 0
        aces = 0
        for r in self.cards:
            if r == "A":
                total += 11
                aces += 1
            else:
                total += VALUES[r]
        while total > 21 and aces > 0:
            total -= 10
            aces -= 1
        return total

    def is_blackjack(self) -> bool:
        return len(self.cards) == 2 and self.value == 21

    def can_split(self) -> bool:
        return len(self.cards) == 2 and self.cards[0] == self.cards[1]

    def can_double(self) -> bool:
        return len(self.cards) == 2


StrategyFn = Callable[[HandState, str], str]


@dataclass
class RoundResult:
    """
    Represents the outcome of a single hand (possibly one of several from
    splits) within a round of Blackjack.
    """

    round_id: int
    hand_number: int
    player_cards: List[str]
    dealer_cards: List[str]
    actions: List[str]
    bet_amount: float
    final_result: str  # "win" | "lose" | "push"
    blackjack: bool
    busted: bool
    strategy_used: str
    bet_mode: str
    true_count_prev_round: float
    running_count_end: float
    true_count_end: float
    cards_remaining: int
    decks_remaining: float


def _dealer_play(dealer: HandState, shoe: Shoe) -> None:
    """Dealer hits until reaching 17 or higher."""
    while dealer.value < 17:
        dealer.cards.append(shoe.pop())
        dealer.actions.append("hit")
    dealer.actions.append("stand")


def _settle(player_value: int, dealer_value: int) -> int:
    """
    Compare player and dealer totals returning:
        +1 for a win, 0 for a push, and −1 for a loss.
    """
    if player_value > 21:
        return -1
    if dealer_value > 21:
        return 1
    if player_value > dealer_value:
        return 1
    if player_value < dealer_value:
        return -1
    return 0


def _bet_from_true_count(tc: float, base: float = 10.0, max_mult: int = 5) -> float:
    """
    Compute the bet multiplier from the true count using a simple ramp:
      tc ≤ 0 → base bet
      tc = 1 → base×2, tc = 2 → base×3, tc = 3 → base×4, tc ≥ 4 → base×5
    """
    if tc <= 0:
        return float(base)
    mult = 1 + int(tc)
    if mult > max_mult:
        mult = max_mult
    return float(base * mult)


def simulate_rounds(
    rounds: int,
    num_decks: int,
    base_bet: float,
    strategy_name: str,
    strategy_fn: StrategyFn,
    bet_mode: str,
    seed: Optional[int] = None,
) -> List[RoundResult]:
    """
    Simulate a sequence of Blackjack rounds.

    Each round updates the Hi‑Lo running and true counts after all hands are
    completed.  Bets for a round are determined by the true count at the end
    of the previous round.  Returns a list of RoundResult instances, one
    per player hand (including hands from splits).
    """
    rng = random.Random(seed)
    shoe = Shoe(num_decks=num_decks, shuffle_seed=seed)
    running_count = 0.0
    total_cards_initial = shoe.cards_remaining()
    true_count_prev = 0.0
    results: List[RoundResult] = []

    for round_id in range(1, rounds + 1):
        # shuffle when the shoe is nearly depleted
        if shoe.cards_remaining() <= 0.25 * total_cards_initial:
            shoe.reshuffle()
            running_count = 0.0
            total_cards_initial = shoe.cards_remaining()
            true_count_prev = 0.0

        if bet_mode == "fixed":
            bet_amount = float(base_bet)
        else:
            bet_amount = _bet_from_true_count(true_count_prev, base=base_bet)

        # Deal initial cards
        player = HandState(cards=[shoe.pop(), shoe.pop()], bet=bet_amount, actions=[])
        dealer = HandState(cards=[shoe.pop(), shoe.pop()], bet=0.0, actions=[])

        seen_this_round: List[str] = list(player.cards) + list(dealer.cards)

        # Immediate blackjack check
        if dealer.is_blackjack():
            # Dealer has blackjack; player pushes if also blackjack otherwise loses
            final = "push" if player.is_blackjack() else "lose"
            res = RoundResult(
                round_id=round_id,
                hand_number=1,
                player_cards=list(player.cards),
                dealer_cards=list(dealer.cards),
                actions=[],
                bet_amount=player.bet,
                final_result=final,
                blackjack=player.is_blackjack(),
                busted=False,
                strategy_used=strategy_name,
                bet_mode=bet_mode,
                true_count_prev_round=round(true_count_prev, 3),
                running_count_end=0.0,
                true_count_end=0.0,
                cards_remaining=0,
                decks_remaining=0.0,
            )
            # Update counts
            delta = sum(hi_lo_value(r) for r in seen_this_round)
            running_count += delta
            true_count_end = running_count / shoe.decks_remaining()
            res.running_count_end = round(running_count, 3)
            res.true_count_end = round(true_count_end, 3)
            res.cards_remaining = shoe.cards_remaining()
            res.decks_remaining = round(shoe.decks_remaining(), 3)
            results.append(res)
            true_count_prev = true_count_end
            continue

        if player.is_blackjack():
            # Player has blackjack and dealer doesn't
            res = RoundResult(
                round_id=round_id,
                hand_number=1,
                player_cards=list(player.cards),
                dealer_cards=list(dealer.cards),
                actions=["stand"],
                bet_amount=player.bet,
                final_result="win",
                blackjack=True,
                busted=False,
                strategy_used=strategy_name,
                bet_mode=bet_mode,
                true_count_prev_round=round(true_count_prev, 3),
                running_count_end=0.0,
                true_count_end=0.0,
                cards_remaining=0,
                decks_remaining=0.0,
            )
            delta = sum(hi_lo_value(r) for r in seen_this_round)
            running_count += delta
            true_count_end = running_count / shoe.decks_remaining()
            res.running_count_end = round(running_count, 3)
            res.true_count_end = round(true_count_end, 3)
            res.cards_remaining = shoe.cards_remaining()
            res.decks_remaining = round(shoe.decks_remaining(), 3)
            results.append(res)
            true_count_prev = true_count_end
            continue

        # Player decisions (including splits)
        hands: List[HandState] = [player]
        hand_index = 0
        while hand_index < len(hands):
            current = hands[hand_index]
            while True:
                action = strategy_fn(current, dealer.cards[0])
                if action == "hit" or (action == "double" and not current.can_double()):
                    current.cards.append(shoe.pop())
                    current.actions.append("hit")
                    seen_this_round.append(current.cards[-1])
                    if current.value > 21:
                        break
                elif action == "stand":
                    current.actions.append("stand")
                    break
                elif action == "double" and current.can_double():
                    current.bet *= 2.0
                    current.doubled = True
                    current.actions.append("double")
                    current.cards.append(shoe.pop())
                    seen_this_round.append(current.cards[-1])
                    current.actions.append("stand")
                    break
                #cambiar logica para resolver cuando no se puede split
                elif action == "split" and current.can_split():
                    # Remove the current hand and create two new hands from the split
                    hands.pop(hand_index)
                    left = HandState(cards=[current.cards[0]], bet=current.bet, actions=["split"])
                    right = HandState(cards=[current.cards[1]], bet=current.bet, actions=["split"])
                    # Each new hand gets one additional card
                    left.cards.append(shoe.pop())
                    right.cards.append(shoe.pop())
                    seen_this_round.extend([left.cards[-1], right.cards[-1]])
                    hands.insert(hand_index, right)
                    hands.insert(hand_index, left)
                    hand_index -= 1
                    break
                else:
                    # Unknown or not allowed action → stand
                    current.actions.append("stand")
                    break
            hand_index += 1

        # Dealer plays
        _dealer_play(dealer, shoe)
        # Add dealer's additional cards to seen
        if len(dealer.cards) > 2:
            seen_this_round.extend(dealer.cards[2:])

        # Settle outcomes for each hand
        hand_counter = 0
        for h in hands:
            hand_counter += 1
            outcome = _settle(h.value, dealer.value)

            if outcome == 0:
                result_str = "push" 
            elif outcome > 0 :
                result_str = "win"
            else:
                result_str = "lose"

            busted = h.value > 21
            blackjack_flag = h.is_blackjack()
            res = RoundResult(
                round_id=round_id,
                hand_number=hand_counter,
                player_cards=list(h.cards),
                dealer_cards=list(dealer.cards),
                actions=list(h.actions),
                bet_amount=h.bet,
                final_result=result_str,
                blackjack=blackjack_flag,
                busted=busted,
                strategy_used=strategy_name,
                bet_mode=bet_mode,
                true_count_prev_round=round(true_count_prev, 3),
                running_count_end=0.0,
                true_count_end=0.0,
                cards_remaining=0,
                decks_remaining=0.0,
            )
            results.append(res)

        # Update Hi‑Lo counts
        delta = sum(hi_lo_value(r) for r in seen_this_round)
        running_count += delta
        true_count = running_count / shoe.decks_remaining()
        # Fill updated counts for all hands of this round
        for res in results[-len(hands):]:
            res.running_count_end = round(running_count, 3)
            res.true_count_end = round(true_count, 3)
            res.cards_remaining = shoe.cards_remaining()
            res.decks_remaining = round(shoe.decks_remaining(), 3)
        true_count_prev = true_count

    return results