"""Runtime hook — registra inicio do executavel empacotado."""

import sys
from datetime import datetime
from pathlib import Path


def _boot_log():
    try:
        if getattr(sys, "frozen", False):
            log_path = Path(sys.executable).resolve().parent / "gestao_vagas.log"
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Boot PyInstaller OK\n")
    except Exception:
        pass


_boot_log()
