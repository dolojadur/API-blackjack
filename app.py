"""
FastAPI application exposing endpoints to simulate hands of Blackjack.

This API merges the game logic and strategy definitions into a single
repository, avoiding the need to import an external simulation package.  It
also eliminates card suits: each card is represented solely by its rank
(e.g. ``"9"`` or ``"K"``), preserving the correct probabilities by
tracking four copies per rank per deck in the shoe.  Bets for each round
are based on the Hi‑Lo true count from the previous round.  The API
supports multiple strategies and returns detailed hand records in a
tabular format.

Usage:
    uvicorn app:app --reload

Endpoints:
    GET  /health       – simple health check
    GET  /strategies   – list of available strategy names
    POST /simulate     – run a simulation and return hand records
"""

from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import List, Optional


from game import simulate_rounds
from strategies import STRATEGIES
from schemas import HandRecord


app = FastAPI(title="Blackjack API", version="1.0.0")


class SimRequest(BaseModel):
    """Parameters for the simulation endpoint."""

    rounds: int = Field(10, ge=1, le=100_000, description="Number of rounds to simulate.")
    num_decks: int = Field(6, ge=1, le=8, description="Number of decks in the shoe.")
    base_bet: float = Field(10.0, gt=0, description="Base bet amount (minimum bet).")
    strategy: str = Field(
        "basic",
        description="Name of the strategy to use. Must be one of the strategies returned by /strategies.",
    )
    seed: Optional[int] = Field(
        None,
        description="Random seed for reproducible simulations. Leave blank for non‑deterministic behaviour.",
    )
    bet_mode: str = Field(
        "fixed",
        description='Betting mode: "fixed" uses base_bet always; "hi-lo" scales by true count.',
    )


@app.get("/health")
def health() -> dict:
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/strategies", response_model=List[str])
def list_strategies() -> List[str]:
    """Return a list of available strategy names."""
    return list(STRATEGIES.keys())


@app.post("/simulate", response_model=List[HandRecord])
def simulate(req: SimRequest) -> List[HandRecord]:
    """
    Run a simulation of `rounds` rounds and return a list of hand records.

    Each record corresponds to a player hand (multiple records may be produced
    per round when the player splits).  The simulation uses the selected
    strategy and updates the Hi‑Lo running and true counts after each round.
    """
    # Validate strategy
    if req.strategy not in STRATEGIES:
        return []

    strategy_fn = STRATEGIES[req.strategy]
    results = simulate_rounds(
        rounds=req.rounds,
        num_decks=req.num_decks,
        base_bet=req.base_bet,
        strategy_name=req.strategy,
        strategy_fn=strategy_fn,
        seed=req.seed,
        bet_mode=req.bet_mode,
    )
    return [HandRecord(**result.__dict__) for result in results]