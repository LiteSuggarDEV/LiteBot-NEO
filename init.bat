if EXIST .\venv\(
    echo "creating venv"
    pip install uv
    uv venv
    uv sync
)
else(
    echo "venv exists"
    uv sync
    source .\venv\Scripts\activate.bat
    python3 ./bot.py
)