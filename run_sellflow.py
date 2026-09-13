"""Ponto de entrada para a versão Windows autônoma do SellFlow."""
import os
import threading
import webbrowser
from pathlib import Path

base_dir = Path(os.getenv("LOCALAPPDATA", Path.home())) / "SellFlow"
os.environ["STANDALONE_MODE"] = "true"
os.environ["STANDALONE_DATA_DIR"] = str(base_dir)

import uvicorn
from app.main import app


def main() -> None:
    base_dir.mkdir(parents=True, exist_ok=True)
    threading.Timer(1.2, lambda: webbrowser.open("http://127.0.0.1:8000/docs")).start()
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")


if __name__ == "__main__":
    main()
