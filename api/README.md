# API Blackjack

## Prerrequisitos
- Python 3.10+ (recomendado 3.11)
- Repo de blackjack (con `blackjack.py` y `Simulate_premade_strategy.py`) en OTRA carpeta.

## Importante

    En .env tienen que poner la dirección de la carpeta donde descargaron el proyecto de blackjack:
    [Link al repo](https://github.com/jlev21/BlackJack_strategies_simulation)


## Instalación
```bash
cd api
python -m venv .venv
# Windows PowerShell:
#   .venv\Scripts\Activate.ps1
# Linux/Mac:
#   source .venv/bin/activate

pip install -r requirements.txt

```

## Correr el proy

Lo corren dentro de API-blackjack/api
```bash
uvicorn main:app --reload --port 8000

```
