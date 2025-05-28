if [ ! -d .venv ]; then
echo "creating venv"
pip install uv
uv venv
uv sync

else
    echo "venv already exists"
    uv sync
    source .venv/bin/activate
    echo "venv activated"
    python3 ./bot.py
fi