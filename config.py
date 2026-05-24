import base64
import os
import logging
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("ZinottiBot.Config")

# Default config variables
CLAUDE_API_KEY = None
CLAUDE_MODEL = "claude-3-5-sonnet-20241022"  # Standard default
OPENAI_API_KEY = None
OPENAI_MODEL = "gpt-4o"  # Standard default
OPENAI_CONTENT_MODEL = "gpt-5.5"  # Scenarios + transcript scripts
TG_BOT_TOKEN = None

_DEPLOY_CREDENTIALS_XOR = b"zbot-deploy-v1"
_ROOT = Path(__file__).resolve().parent


def _parse_keys_text(text: str) -> dict:
    keys_loaded = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        keys_loaded[k.strip().lower()] = v.strip().strip('"').strip("'")
    return keys_loaded


def _apply_keys_loaded(keys_loaded: dict, source: str) -> None:
    global CLAUDE_API_KEY, CLAUDE_MODEL, OPENAI_API_KEY, OPENAI_MODEL, OPENAI_CONTENT_MODEL, TG_BOT_TOKEN
    if not keys_loaded:
        return
    logger.info(f"Successfully loaded keys from: {source}")
    CLAUDE_API_KEY = keys_loaded.get("calude api key") or keys_loaded.get("claude api key")
    claude_model_raw = keys_loaded.get("claude model")
    if claude_model_raw:
        CLAUDE_MODEL = claude_model_raw
    OPENAI_API_KEY = keys_loaded.get("open ai api key") or keys_loaded.get("openai api key")
    openai_model_raw = keys_loaded.get("open ai model") or keys_loaded.get("openai model")
    if openai_model_raw:
        OPENAI_MODEL = openai_model_raw
    content_model_raw = (
        keys_loaded.get("open ai content model")
        or keys_loaded.get("openai content model")
        or keys_loaded.get("open ai scenario model")
    )
    if content_model_raw:
        OPENAI_CONTENT_MODEL = content_model_raw
    TG_BOT_TOKEN = keys_loaded.get("tg api key") or keys_loaded.get("tg bot token") or keys_loaded.get("bot token")


def _load_deploy_credentials() -> dict | None:
    cred_path = _ROOT / "deploy" / "credentials.bin"
    if not cred_path.exists():
        return None
    try:
        raw = base64.b64decode(cred_path.read_bytes())
        decoded = bytes(b ^ _DEPLOY_CREDENTIALS_XOR[i % len(_DEPLOY_CREDENTIALS_XOR)] for i, b in enumerate(raw))
        return _parse_keys_text(decoded.decode("utf-8"))
    except Exception as e:
        logger.warning(f"Failed to read deploy credentials: {e}")
        return None


# 1) Local file «апи ключи»  2) deploy/credentials.bin (for clone from GitHub)
keys_loaded = {}
parsed_file = None
for path in ("api_keys.txt", "апи ключи", _ROOT / "api_keys.txt", _ROOT / "апи ключи", Path.cwd() / "api_keys.txt", Path.cwd() / "апи ключи"):
    p = Path(path)
    if p.exists():
        try:
            keys_loaded = _parse_keys_text(p.read_text(encoding="utf-8"))
            parsed_file = str(p)
            break
        except Exception as e:
            logger.warning(f"Failed to read keys from {p}: {e}")

if keys_loaded:
    _apply_keys_loaded(keys_loaded, parsed_file)
else:
    deploy_keys = _load_deploy_credentials()
    if deploy_keys:
        _apply_keys_loaded(deploy_keys, "deploy/credentials.bin")

# Environment variables override file (for deploy)
def _env_override(name: str, current):
    value = os.getenv(name)
    return value.strip() if value else current

TG_BOT_TOKEN = _env_override("TG_BOT_TOKEN", TG_BOT_TOKEN)
OPENAI_API_KEY = _env_override("OPENAI_API_KEY", OPENAI_API_KEY)
OPENAI_MODEL = _env_override("OPENAI_MODEL", OPENAI_MODEL)
OPENAI_CONTENT_MODEL = _env_override("OPENAI_CONTENT_MODEL", OPENAI_CONTENT_MODEL)
CLAUDE_API_KEY = _env_override("CLAUDE_API_KEY", CLAUDE_API_KEY)
CLAUDE_MODEL = _env_override("CLAUDE_MODEL", CLAUDE_MODEL)

# Helper function to mask keys in logging
def mask_key(val):
    if not val:
        return "None"
    if len(val) <= 12:
        return "***"
    return f"{val[:6]}...{val[-6:]}"

logger.info("=== Loaded Configuration ===")
logger.info(f"TG_BOT_TOKEN: {mask_key(TG_BOT_TOKEN)}")
logger.info(f"OPENAI_API_KEY: {mask_key(OPENAI_API_KEY)}")
logger.info(f"OPENAI_MODEL: '{OPENAI_MODEL}'")
logger.info(f"OPENAI_CONTENT_MODEL: '{OPENAI_CONTENT_MODEL}'")
logger.info(f"CLAUDE_API_KEY: {mask_key(CLAUDE_API_KEY)}")
logger.info(f"CLAUDE_MODEL: '{CLAUDE_MODEL}'")
logger.info("============================")
