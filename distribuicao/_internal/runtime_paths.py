"""Caminhos da aplicação em desenvolvimento e em executável empacotado."""

from pathlib import Path
import sys


def is_frozen() -> bool:
    return getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")


def app_base_dir() -> Path:
    """Pasta com os arquivos da aplicação (empacotados ou do projeto)."""
    if is_frozen():
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent


def data_dir() -> Path:
    """Pasta persistente ao lado do .exe (dados do usuário)."""
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def get_db_path() -> Path:
    """Caminho do banco SQLite; a pasta é criada se não existir."""
    path = data_dir() / "vagas.db"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def get_playwright_browsers_path() -> Path | None:
    """Pasta com Chromium empacotado (modo executável)."""
    if not is_frozen():
        return None
    bundled = data_dir() / "ms-playwright"
    return bundled if bundled.is_dir() else None
