from sqlalchemy import Column, Integer, String, Boolean, Numeric, ForeignKey, DateTime, func, Index
from sqlalchemy.orm import relationship
from database import Base

class Match(Base):
    __tablename__ = "matches"
    id = Column(String, primary_key=True)
    strategy = Column(String, nullable=False, default="basic")  # estrategia usada en ese match
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    plays = relationship("Play", back_populates="match", cascade="all, delete-orphan")

class Play(Base):
    __tablename__ = "plays"
    id = Column(Integer, primary_key=True, autoincrement=True)
    match_id = Column(String, ForeignKey("matches.id", ondelete="CASCADE"), index=True, nullable=False)
    dealer_card = Column(String, nullable=False)
    player_card = Column(String, nullable=False)
    doubled = Column(Boolean, default=False, nullable=False)
    won = Column(Boolean, default=False, nullable=False)
    bet_amount = Column(Numeric(12, 2), nullable=False, default=0)
    payout_amount = Column(Numeric(12, 2), nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    match = relationship("Match", back_populates="plays")

# índice útil para lecturas por match y orden temporal
Index("ix_plays_match_created", Play.match_id, Play.created_at)
