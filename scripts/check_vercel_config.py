"""Validate local config against Vercel's official schema; never deploy."""
import json
from pathlib import Path
import httpx
from jsonschema import validators

if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    response = httpx.get("https://openapi.vercel.sh/vercel.json", timeout=30)
    response.raise_for_status()
    schema = response.json()
    config = json.loads((root / "vercel.json").read_text())
    errors = list(validators.validator_for(schema)(schema).iter_errors(config))
    if errors:
        for error in errors:
            print(f"Configuration error at {list(error.path)}: {error.message}")
        raise SystemExit(1)
    print("Vercel official schema: valid. No cloud deployment performed.")
