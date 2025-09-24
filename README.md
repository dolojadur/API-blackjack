# API de Blackjack

Este repositorio unifica la lógica para simular manos de Blackjack con una
aplicación FastAPI. A diferencia de la separación original entre una API y un
paquete de simulación independiente, aquí todas las reglas del juego,
estrategias y definiciones de la API viven juntas en una estructura compacta y
mantenible.

## Características

- **Cartas sin palos:** Cada carta está representada solo por su rango (ej. `"K"`),
  mientras que el shoe mantiene la distribución correcta de probabilidades
  almacenando cuatro copias de cada rango por mazo.
- **Conteo Hi-Lo:** El conteo acumulado Hi-Lo y el conteo verdadero se actualizan
  después de cada ronda. Las apuestas de la siguiente ronda dependen del conteo
  verdadero de la ronda anterior.
- **División y doblaje:** La simulación soporta acciones básicas como dividir
  pares y doblar.
- **Múltiples estrategias:** Se incluyen algunas estrategias de ejemplo
  (simplest, random, basic), y se pueden agregar más fácilmente en
  `strategies.py`.
- **Un solo punto de entrada de API:** Expone un endpoint POST para simular un
  número de rondas y devolver los datos resultantes de las manos.

## Ejecución

Para instalar las dependencias y correr la API localmente:

```bash
pip install -r requirements.txt

# Iniciar el servidor
uvicorn app:app --reload

# Verificar que está corriendo
curl http://localhost:8000/health
```

## Uso

La API expone los siguientes endpoints:

### `GET /health`

Chequeo de salud simple que devuelve `{ "status": "ok" }`.

### `GET /strategies`

Devuelve una lista con los nombres de las estrategias disponibles. Usá uno de
estos nombres como valor del campo `strategy` en las requests de simulación.

### `POST /simulate`

Cuerpo de la request (JSON):

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

Campos:

- `rounds` (int): número de rondas a jugar (≥1).
- `num_decks` (int): número de mazos en el shoe (entre 1 y 8).
- `base_bet` (float): monto de la apuesta base (debe ser >0).
- `strategy` (str): nombre de la estrategia (ver `/strategies`).
- `seed` (opcional int): semilla aleatoria para corridas determinísticas.
- `bet_mode`: modo en la que se apuesta. "fixed" la apuesta no cambia, "Hi-Lo" la apuesta aumenta segun la true count

Respuesta: un arreglo de objetos, cada uno representando una mano del jugador.
Ver `schemas.py` para la descripción de campos, incluyendo los conteos Hi-Lo e
indicadores de blackjack o bust.

```bash
curl -X POST http://localhost:8000/simulate \
     -H "Content-Type: application/json" \
     -d '{"rounds":5,"num_decks":6,"base_bet":10,"strategy":"basic","seed":42, "bet_mode": "fixed"}'
```
## Para Windows
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

## Modificación

Para agregar una nueva estrategia, implementá una función en `strategies.py` con la firma `(hand: HandState, dealer_up: str) -> str`
y agregala al diccionario `STRATEGIES`. Para modificar el esquema de apuestas o el sistema de
conteo, editá las funciones correspondientes en `game.py`.
