"""One-time: encode «апи ключи» -> deploy/credentials.bin (not plain text)."""
import base64
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KEYS_CANDIDATES = [ROOT / "api_keys.txt", ROOT / "апи ключи"]
OUT = ROOT / "deploy" / "credentials.bin"
XOR_KEY = b"zbot-deploy-v1"


def xor_bytes(data: bytes, key: bytes) -> bytes:
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))


def main() -> None:
    keys_path = next((p for p in KEYS_CANDIDATES if p.exists()), None)
    if not keys_path:
        raise SystemExit(f"Missing keys file. Create api_keys.txt or «апи ключи» in {ROOT}")
    raw = keys_path.read_bytes()
    encoded = base64.b64encode(xor_bytes(raw, XOR_KEY))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_bytes(encoded)
    print(f"Wrote {OUT} ({len(encoded)} bytes)")


if __name__ == "__main__":
    main()
