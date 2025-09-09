"""
Pydantic data models for API responses.

These classes mirror the dataclasses returned by the simulation functions
and ensure that responses are properly validated and serialised by
FastAPI.
"""

from pydantic import BaseModel, Field
from typing import List


class HandRecord(BaseModel):
    """
    Represents a single player hand within a Blackjack round for API
    responses.
    """

    round_id: int
    hand_number: int
    player_cards: List[str] = Field(..., description="The ranks of the player's cards in this hand.")
    dealer_cards: List[str] = Field(..., description="The ranks of the dealer's cards at the end of the round.")
    actions: List[str] = Field(..., description="The sequence of actions taken by the player (e.g. hit, stand).")
    bet_amount: float = Field(..., description="The total bet placed on this hand (includes doubling).")
    final_result: str = Field(..., description="Outcome of the hand: win, lose, or push.")
    blackjack: bool = Field(..., description="Whether the player has a natural blackjack.")
    busted: bool = Field(..., description="Whether the player busted in this hand.")
    strategy_used: str = Field(..., description="Name of the strategy employed for this simulation.")
    bet_mode: str = Field(..., description='Betting mode used: "fixed" or "hi-lo".')
    true_count_prev_round: float = Field(..., description="True count prior to betting in this round.")
    running_count_end: float = Field(..., description="Hi‑Lo running count after this round is completed.")
    true_count_end: float = Field(..., description="True count after this round is completed.")
    cards_remaining: int = Field(..., description="Number of cards left in the shoe after the round.")
    decks_remaining: float = Field(..., description="Number of decks remaining (cards_remaining/52).")