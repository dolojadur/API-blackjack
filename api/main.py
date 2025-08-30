# (arriba del todo)
import os, sys, random
os.environ.setdefault("MPLBACKEND", "Agg")  # <- agregar esta línea
from typing import List, Optional


# NUEVO: importar el lector de .env
from config import get_blackjack_repo_dir

# =========================
# Importar tu repo de blackjack (en OTRA carpeta)
# AHORA: lo leemos desde archivo .env
# =========================
BJK_DIR = get_blackjack_repo_dir()
if BJK_DIR not in sys.path:
    sys.path.append(BJK_DIR)


# Importa tu lógica del proyecto de GitHub
from blackjack import Deck, Hand  # tu archivo blackjack.py
import Simulate_premade_strategy as pre  # tus estrategias

from fastapi import FastAPI, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import select

from database import Base, engine, get_db
from models import Play, Match
from schemas import PlayOut

app = FastAPI(title="Blackjack Plays API", version="1.3.0")
Base.metadata.create_all(bind=engine)

# Estrategias disponibles desde tu repo
AVAILABLE_STRATEGIES = {
    "simplest_strategy": pre.simplest_strategy,
    "random_strategy": pre.random_strategy,
    "basic_strategy": pre.basic_strategy,
    "basic_strategy_no_split": pre.basic_strategy_no_split,
    "basic_strategy_no_aces": pre.basic_strategy_no_aces,
    "basic_strategy_no_splits_or_aces": pre.basic_strategy_no_splits_or_aces,
}
STRATEGY_NAMES = list(AVAILABLE_STRATEGIES.keys())

def choose_random_strategy_name() -> str:
    return random.choice(STRATEGY_NAMES)

def play_hand_detailed(strategy_fn, initial_bet: float, deck: Deck):
    """
    Juega UNA mano usando tu engine, devolviendo:
    - dealer upcard
    - primera carta del jugador
    - si se dobló alguna mano
    - profit neto (considerando splits y dobles)
    - bet_total y payout_total (para auditar)
    """
    player_hand = Hand(initial_bet)
    dealer_hand = Hand(0)

    # deal inicial
    player_hand.add_card(deck.deal())
    player_hand.add_card(deck.deal())
    dealer_hand.add_card(deck.deal())
    dealer_hand.add_card(deck.deal())

    def pretty(card):
        return f"{card[0]} of {card[1]}"

    dealer_up = pretty(dealer_hand.cards[0])
    player_first = pretty(player_hand.cards[0])
    any_double = False

    # Blackjack inmediatos
    if dealer_hand.is_blackjack():
        total = 0.0 if player_hand.is_blackjack() else -1.0 * initial_bet
        bet_total = float(initial_bet)
        payout_total = bet_total + total
        return {
            "dealer_card": dealer_up,
            "player_card": player_first,
            "doubled": any_double,
            "profit": float(total),
            "bet_total": bet_total,
            "payout_total": float(payout_total),
        }

    if player_hand.is_blackjack():
        total = initial_bet * 1.5
        bet_total = float(initial_bet)
        payout_total = bet_total + total
        return {
            "dealer_card": dealer_up,
            "player_card": player_first,
            "doubled": any_double,
            "profit": float(total),
            "bet_total": bet_total,
            "payout_total": float(payout_total),
        }

    hands = [player_hand]
    hand_index = 0

    while hand_index < len(hands):
        hand = hands[hand_index]
        while True:
            action = strategy_fn(hand, dealer_hand.cards[0])
            if action == 'hit':
                hand.add_card(deck.deal())
                if hand.value > 21:
                    break
            elif action == 'stand':
                break
            elif action == 'double' and hand.can_double():
                hand.double_bet()
                any_double = True
                hand.add_card(deck.deal())
                break
            elif action == 'split' and hand.can_split():
                hands.pop(hand_index)
                h1 = Hand(hand.bet_amount)
                h2 = Hand(hand.bet_amount)
                h1.add_card(hand.cards[0])
                h2.add_card(hand.cards[1])
                h1.add_card(deck.deal())
                h2.add_card(deck.deal())
                hands.insert(hand_index, h1)
                hands.insert(hand_index + 1, h2)
                hand_index -= 1
                break
            else:
                break
        hand_index += 1

    # turno dealer
    while dealer_hand.value < 17:
        dealer_hand.add_card(deck.deal())

    # settle
    total_profit_loss = 0.0
    for hand in hands:
        if hand.value > 21:
            total_profit_loss -= float(hand.bet_amount)
        elif dealer_hand.value > 21 or hand.value > dealer_hand.value:
            total_profit_loss += float(hand.bet_amount)
        elif hand.value < dealer_hand.value:
            total_profit_loss -= float(hand.bet_amount)
        else:
            pass  # push

    bet_total = float(sum(float(h.bet_amount) for h in hands))
    payout_total = bet_total + total_profit_loss

    return {
        "dealer_card": dealer_up,
        "player_card": player_first,
        "doubled": any_double,
        "profit": float(total_profit_loss),
        "bet_total": bet_total,
        "payout_total": float(payout_total),
    }

def generar_manos(match_id: str, n: int, db: Session, num_decks: int = 6, apuesta: float = 50.0):
    # Si no existe match, crearlo con estrategia aleatoria
    m = db.get(Match, match_id)
    if not m:
        strat_name = choose_random_strategy_name()
        m = Match(id=match_id, strategy=strat_name)
        db.add(m)
        db.flush()
    else:
        strat_name = m.strategy

    strategy_fn = AVAILABLE_STRATEGIES[strat_name]
    deck = Deck(num_decks)

    nuevas = []
    for _ in range(n):
        info = play_hand_detailed(strategy_fn, apuesta, deck)
        nuevas.append(
            Play(
                match_id=match_id,
                dealer_card=info["dealer_card"],
                player_card=info["player_card"],
                doubled=info["doubled"],
                won=bool(info["profit"] > 0),
                bet_amount=info["bet_total"],
                payout_amount=info["payout_total"],
            )
        )
    db.add_all(nuevas)
    db.commit()

@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/jugadas", response_model=List[PlayOut], summary="Lista jugadas (incluye estrategia del match)")
def listar_jugadas(
    match_id: Optional[str] = Query(default=None, description="ID del partido"),
    autogenerar: bool = Query(default=False, description="Si no existe el match, crearlo y poblarlo"),
    n_manos: int = Query(default=50, ge=1, le=10000, description="Cantidad a generar si autogenerar=true"),
    limit: int = Query(default=500, ge=1, le=10000),
    desde_id: Optional[int] = Query(default=None, description="Paginación: id > desde_id"),
    num_decks: int = Query(default=6, ge=1, le=8, description="N° de mazos"),
    apuesta: float = Query(default=50.0, gt=0, description="Apuesta base"),
    db: Session = Depends(get_db),
):
    if autogenerar and match_id and not db.get(Match, match_id):
        generar_manos(match_id=match_id, n=n_manos, db=db, num_decks=num_decks, apuesta=apuesta)

    stmt = select(Play)
    if match_id:
        stmt = stmt.where(Play.match_id == match_id)
    if desde_id:
        stmt = stmt.where(Play.id > desde_id)
    stmt = stmt.order_by(Play.id.asc()).limit(limit)

    filas = db.execute(stmt).scalars().all()

    # cache estrategia por match
    strat_cache = {}
    out = []
    for p in filas:
        s = strat_cache.get(p.match_id)
        if s is None:
            m = db.get(Match, p.match_id)
            s = m.strategy if m else "unknown"
            strat_cache[p.match_id] = s

        profit = float((p.payout_amount or 0) - (p.bet_amount or 0))
        out.append(
            PlayOut(
                match_id=p.match_id,
                strategy=s,
                dealer_card=p.dealer_card,
                player_card=p.player_card,
                doubled=bool(p.doubled),
                won=bool(p.won),
                profit=profit,
            )
        )
    return out
