# Blackjack API (Unified)

This repository merges the logic for simulating Blackjack hands with a
FastAPI application.  Unlike the original separation of an API and a
separate simulation package, all the game rules, strategies, and API
definitions live together here in a compact and maintainable structure.

## Features

- **Suitless cards:** Each card is represented only by its rank (e.g. `"K"`),
  while the shoe maintains the correct probability distribution by storing
  four copies of each rank per deck.
- **Hi‑Lo counting:** The running Hi‑Lo count and true count are updated
  after each round.  Bets for the next round depend on the true count from
  the previous round.
- **Splitting and doubling:** The simulation supports basic actions
  including splitting pairs and doubling down.
- **Multiple strategies:** A few example strategies are provided (simplest,
  random, basic), and more can be added easily in `strategies.py`.
- **Single API entrypoint:** Exposes a POST endpoint to simulate a number of
  rounds and return the resulting hand data.

## Running

To install dependencies and run the API locally:

```bash
pip install -r requirements.txt

# Start the server
uvicorn app:app --reload

# Check it is running
curl http://localhost:8000/health
```

## Usage

The API exposes the following endpoints:

### `GET /health`

Simple health check returning `{ "status": "ok" }`.

### `GET /strategies`

Returns a list of available strategy names.  Use one of these names as
the `strategy` field in simulation requests.

### `POST /simulate`

Request body (JSON):

```json
{
  "rounds": 100,
  "num_decks": 6,
  "base_bet": 10,
  "strategy": "basic",
  "seed": 42,
  "bet_mode:" "fixed"
}
```

Fields:

- `rounds` (int): number of rounds to play (≥1).
- `num_decks` (int): number of decks in the shoe (between 1 and 8).
- `base_bet` (float): base bet amount (must be >0).
- `strategy` (str): name of the strategy (see `/strategies`).
- `seed` (optional int): random seed for deterministic runs.
- `bet_mode`: modo en la que se apuesta. "fixed" la apuesta no cambia, "Hi-Lo" la apuesta aumenta segun la true count

Response: an array of objects, each representing a player hand.  See
`schemas.py` for field descriptions, including the Hi‑Lo counts and
indicators for blackjack or busts.

```bash
curl -X POST http://localhost:8000/simulate \
     -H "Content-Type: application/json" \
     -d '{"rounds":5,"num_decks":6,"base_bet":10,"strategy":"basic","seed":42, "bet_mode": "fixed"}'
```

```Powershell
$headers = @{ "Content-Type" = "application/json" }
$body = '{
  "rounds": 5,
  "num_decks": 6,
  "base_bet": 10,
  "strategy": "basic",
  "seed": 42,
  "bet_mode": "fixed"
}'

Invoke-WebRequest -Uri "http://localhost:8000/simulate" -Method POST -Headers $headers -Body $body
```

Recomiendo usar Postman para probar los endpoints.

## Modifying

To add a new strategy, implement a function in `strategies.py` with
signature `(hand: HandState, dealer_up: str) -> str` and add it to the
`STRATEGIES` dictionary.  To modify the betting scheme or counting system,
edit the corresponding functions in `game.py`.