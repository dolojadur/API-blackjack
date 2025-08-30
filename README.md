# 🎰 API Blackjack

API en **FastAPI** que simula jugadas de blackjack usando las **estrategias** del repo externo y expone un endpoint para que otras apps (p. ej. **Airflow**) consuman los datos.

---

## 📦 Prerrequisitos

* **Python 3.10+** (recomendado **3.11**)
* Repo de estrategias (con `blackjack.py` y `Simulate_premade_strategy.py`) en **otra carpeta**
  → [BlackJack\_strategies\_simulation](https://github.com/jlev21/BlackJack_strategies_simulation)

---

## ⚙️ Configuración de entorno

1. Crear archivo `.env` dentro de `api/` con la **ruta local** del repo de estrategias:

```ini
# api/.env
# Ejemplo Windows:
BLACKJACK_REPO_DIR=C:\Users\tu_usuario\Documents\BlackJack_strategies_simulation

# Ejemplo Linux/Mac:
# BLACKJACK_REPO_DIR=/home/tu_usuario/BlackJack_strategies_simulation
```

> La API **no** lee variables del sistema: usa este `.env`.

---

## 🧩 Instalación

```bash
cd api
python -m venv .venv

# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# Linux/Mac
# source .venv/bin/activate

pip install -r requirements.txt
```

> Si tu repo de estrategias requiere librerías adicionales y aparece un error tipo
> `ModuleNotFoundError: No module named 'matplotlib'`, instalá:
>
> ```bash
> pip install numpy matplotlib
> ```

---

## ▶️ Correr la API

```bash
# desde la carpeta: API-blackjack/api
uvicorn main:app --reload --port 8000
```

* Docs interactivas: `http://127.0.0.1:8000/docs`
* Healthcheck: `http://127.0.0.1:8000/health`

---

## 🔌 Endpoints

### `GET /health`

Verifica que el servicio esté vivo.

```json
{ "status": "ok" }
```

### `GET /jugadas`

Genera (o lee) jugadas para un **match** y devuelve la lista.

**Query params:**

* `match_id` *(string)*: identificador del partido.
* `autogenerar` *(true/false)*: si no existe el match, lo crea y simula.
* `n_manos` *(int)*: cantidad de jugadas a generar si `autogenerar=true` (por defecto 50).
* `limit` *(int)*: tope de filas a devolver (por defecto 500).
* `desde_id` *(int)*: paginado (devuelve jugadas con `id > desde_id`).
* `num_decks` *(int)*: cantidad de mazos para el simulador (por defecto 6).
* `apuesta` *(float)*: apuesta base por mano (por defecto 50.0).

**Respuesta (por ítem):**

```json
{
  "match_id": "run-20250830",
  "strategy": "basic_strategy",
  "dealer_card": "Queen of Hearts",
  "player_card": "Ace of Clubs",
  "doubled": false,
  "won": true,
  "profit": 75.0
}
```

**Ejemplo:**

```bash
curl "http://127.0.0.1:8000/jugadas?match_id=demo-001&autogenerar=true&n_manos=25&limit=1000"
```

> La **estrategia** se elige **al azar** cuando se crea un `match_id` nuevo y queda fija para ese partido.

---

## 🗂️ Estructura del proyecto

```
API-blackjack/
└─ api/
   ├─ .env                 # ruta local al repo de estrategias
   ├─ config.py            # lector de .env (sin usar OS env)
   ├─ database.py          # engine y session (SQLite por defecto)
   ├─ main.py              # FastAPI + endpoints
   ├─ models.py            # SQLAlchemy (Match, Play)
   ├─ schemas.py           # Pydantic (respuesta)
   ├─ requirements.txt     # dependencias
   └─ README.md            # este archivo
```

---

## 🤝 Uso con Airflow (opcional, dev local con Astro)

1. API arriba (`uvicorn ...`).
2. `astro dev start`.
3. En Airflow **Admin → Connections** crear `blackjack_api`:

   * Type: **HTTP**
   * Host: `host.docker.internal`
   * Schema: `http`
   * Port: `8000`
4. Ejecutar el DAG (por ejemplo `blackjack_pipeline`).

Archivos generados por el DAG:

```
include/exports/blackjack/<run_id>_jugadas.json
include/exports/blackjack/<run_id>_jugadas.csv
```

---

## 🆘 Troubleshooting

* **`ModuleNotFoundError: matplotlib`**
  `pip install numpy matplotlib`

* **La API no arranca y menciona BLACKJACK\_REPO\_DIR**
  Revisá `api/.env` y que la ruta apunte al folder donde está `blackjack.py`.

* **Desde Airflow no llega a la API**
  Verificá la conexión `blackjack_api` y que la API esté en `http://127.0.0.1:8000`. En contenedores, el host se referencia como `http://host.docker.internal:8000`.
