import os
import logging

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

# Attempt to locate and parse "апи ключи"
possible_paths = [
    "апи ключи",
    os.path.join(os.path.dirname(__file__), "апи ключи"),
    os.path.join(os.getcwd(), "апи ключи"),
]

keys_loaded = {}
parsed_file = None

for path in possible_paths:
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip().lower()
                        v = v.strip().strip('"').strip("'")
                        keys_loaded[k] = v
            parsed_file = path
            break
        except Exception as e:
            logger.warning(f"Failed to read keys from {path}: {e}")

if keys_loaded:
    logger.info(f"Successfully parsed keys from file: {parsed_file}")
    
    # Map raw fields with typos accounted for
    CLAUDE_API_KEY = keys_loaded.get("calude api key") or keys_loaded.get("claude api key")
    CLAUDE_MODEL_RAW = keys_loaded.get("claude model")
    if CLAUDE_MODEL_RAW:
        CLAUDE_MODEL = CLAUDE_MODEL_RAW
        
    OPENAI_API_KEY = keys_loaded.get("open ai api key") or keys_loaded.get("openai api key")
    OPENAI_MODEL_RAW = keys_loaded.get("open ai model") or keys_loaded.get("openai model")
    if OPENAI_MODEL_RAW:
        OPENAI_MODEL = OPENAI_MODEL_RAW

    OPENAI_CONTENT_MODEL_RAW = (
        keys_loaded.get("open ai content model")
        or keys_loaded.get("openai content model")
        or keys_loaded.get("open ai scenario model")
    )
    if OPENAI_CONTENT_MODEL_RAW:
        OPENAI_CONTENT_MODEL = OPENAI_CONTENT_MODEL_RAW
        
    TG_BOT_TOKEN = keys_loaded.get("tg api key") or keys_loaded.get("tg bot token") or keys_loaded.get("bot token")

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
