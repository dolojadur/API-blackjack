from pydantic import BaseModel, Field

class PlayOut(BaseModel):
    match_id: str
    strategy: str
    dealer_card: str
    player_card: str
    doubled: bool
    won: bool
    profit: float = Field(..., description="payout_amount - bet_amount")

    class Config:
        from_attributes = True
