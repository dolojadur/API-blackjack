from pathlib import Path
from dotenv import dotenv_values

def _load_env_from_files():
    """
    Carga variables desde:
    - api/.env
    - <raiz_del_repo>/.env
    Sin escribir en os.environ (solo en memoria).
    """
    here = Path(__file__).parent
    candidates = [here / ".env", here.parent / ".env"]
    env = {}
    for p in candidates:
        if p.exists():
            env.update(dotenv_values(p))
    return env

def get_blackjack_repo_dir() -> str:
    env = _load_env_from_files()
    repo_dir = env.get("BLACKJACK_REPO_DIR")
    if not repo_dir or not repo_dir.strip():
        raise RuntimeError(
            "Falta BLACKJACK_REPO_DIR en api/.env (o en <raiz>/.env). "
            "Ej: BLACKJACK_REPO_DIR=C:\\ruta\\al\\repo\\blackjack"
        )
    # Normalizamos y expandimos ~ si lo hubiera
    p = Path(repo_dir).expanduser()
    return str(p)
