"""
Ponto de entrada para o executável Gestão de Vagas.
Use preferencialmente: Iniciar Gestao de Vagas.bat
"""

import os
import sys
import traceback
from datetime import datetime
from pathlib import Path


PORTA = 8501
URL_APP = f"http://localhost:{PORTA}"


def _pasta_exe():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def _log(msg):
    try:
        with open(_pasta_exe() / "gestao_vagas.log", "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    except Exception:
        pass


def _pausar(msg="Pressione Enter para encerrar..."):
    try:
        print(msg)
        input()
    except Exception:
        pass


def _preparar_ambiente():
    base = Path(sys._MEIPASS) if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
    os.chdir(base)
    if str(base) not in sys.path:
        sys.path.insert(0, str(base))

    if getattr(sys, "frozen", False):
        validators_json = base / "plotly" / "validators" / "_validators.json"
        if not validators_json.is_file():
            raise FileNotFoundError(
                "Pacote incompleto: falta o arquivo plotly/validators/_validators.json em "
                f"{validators_json.parent}.\n"
                "Copie a pasta 'distribuicao' INTEIRA para o outro computador "
                "(GestaoVagas.exe, _internal e Iniciar Gestao de Vagas.bat juntos)."
            )

        from runtime_paths import get_playwright_browsers_path

        browsers_path = get_playwright_browsers_path()
        if browsers_path:
            os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(browsers_path)

    os.environ["STREAMLIT_GLOBAL_DEVELOPMENT_MODE"] = "false"
    os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"
    os.environ["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
    os.environ["STREAMLIT_SERVER_PORT"] = str(PORTA)
    os.environ["STREAMLIT_SERVER_ADDRESS"] = "localhost"


def _inicializar_banco():
    from database import db

    db.init_db()
    _log(f"Banco inicializado em: {db.DB_PATH}")


def _abrir_navegador():
    import threading
    import time
    import urllib.request
    import webbrowser

    def _tarefa():
        for _ in range(90):
            try:
                with urllib.request.urlopen(f"{URL_APP}/_stcore/health", timeout=2) as resp:
                    if resp.status == 200:
                        _log("Servidor online. Abrindo navegador.")
                        webbrowser.open(URL_APP)
                        return
            except Exception:
                time.sleep(1)
        _log("Servidor nao respondeu a tempo para abrir o navegador.")

    threading.Thread(target=_tarefa, daemon=True).start()


def main():
    import threading  # noqa: F401 — usado indiretamente

    _log("Iniciando Gestao de Vagas...")
    _preparar_ambiente()
    _inicializar_banco()
    _abrir_navegador()

    app_py = Path(sys._MEIPASS) / "app.py" if getattr(sys, "frozen", False) else Path(__file__).parent / "app.py"
    if not app_py.exists():
        raise FileNotFoundError(f"Arquivo app.py nao encontrado em: {app_py}")

    _log(f"Subindo Streamlit com: {app_py}")

    sys.argv = [
        "streamlit",
        "run",
        str(app_py),
        "--server.headless",
        "true",
        "--browser.gatherUsageStats",
        "false",
        "--server.port",
        str(PORTA),
        "--server.address",
        "localhost",
        "--global.developmentMode",
        "false",
    ]

    from streamlit.web import cli as stcli

    print("=" * 52)
    print("  Gestao de Vagas")
    print("=" * 52)
    print(f"  URL: {URL_APP}")
    print("  Aguarde o navegador abrir...")
    print("  NAO FECHE esta janela enquanto usar o sistema.")
    print("=" * 52)
    print()

    stcli.main()


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as exc:
        erro = traceback.format_exc()
        _log(f"ERRO FATAL:\n{erro}")
        print("\n[ERRO] Falha ao iniciar o sistema:")
        print(exc)
        print("\nDetalhes gravados em gestao_vagas.log")
        if getattr(sys, "frozen", False):
            _pausar()
        sys.exit(1)
