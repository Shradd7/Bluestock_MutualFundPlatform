"""Fetch current NAV history from mfapi.in and save raw CSV extracts."""

from pathlib import Path

import pandas as pd

try:
    import requests
except ImportError:  # permits the script to run with the bundled runtime offline
    requests = None
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent
RAW_DIR = ROOT / "data" / "raw"
SCHEMES = {
    "125497": "HDFC Top 100 Direct",
    "119551": "SBI Bluechip",
    "120503": "ICICI Bluechip",
    "118632": "Nippon Large Cap",
    "119092": "Axis Bluechip",
    "120841": "Kotak Bluechip",
}


def fetch_scheme(code: str, name: str) -> pd.DataFrame:
    url = f"https://api.mfapi.in/mf/{code}"
    if requests is not None:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        payload = response.json()
    else:
        request = Request(url, headers={"User-Agent": "Bluestock-Day1/1.0"})
        with urlopen(request, timeout=30) as response:
            import json
            payload = json.load(response)
    meta = payload.get("meta", {})
    rows = payload.get("data", [])
    if not rows:
        raise ValueError(f"No NAV records returned for scheme {code}")
    frame = pd.DataFrame(rows)
    frame.insert(0, "scheme_code", code)
    frame.insert(1, "scheme_name", name)
    for key, value in meta.items():
        if key not in frame.columns:
            frame[key] = value
    output = RAW_DIR / f"nav_{code}.csv"
    frame.to_csv(output, index=False)
    print(f"{name} ({code}): {frame.shape} -> {output}")
    print(frame.head().to_string(index=False))
    return frame


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    for code, name in SCHEMES.items():
        try:
            fetch_scheme(code, name)
        except Exception as exc:
            print(f"ERROR fetching/parsing {code} ({name}): {type(exc).__name__}: {exc}")


if __name__ == "__main__":
    main()
