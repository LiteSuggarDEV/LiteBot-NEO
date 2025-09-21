from base64 import b64decode
from json import load
from pathlib import Path


def load_bad_words() -> list[str]:
    with open(Path(__file__).parent / "badwords.json", encoding="utf-8") as f:
        b64_words: list[str] = load(f)
    return [b64decode(word.encode("utf-8")).decode("utf-8") for word in b64_words]


BAD_WORDS = load_bad_words()
BAD_WORDS.sort()

print(f"加载了{len(BAD_WORDS)} 个内置敏感词")


def check_bad_words(text: str) -> bool:
    return any(word in text for word in BAD_WORDS if text)
