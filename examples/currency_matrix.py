"""
Loop every Template-line currency preset, apply at runtime, assert format state.

  BASE_URL=http://localhost:5173 python currency_matrix.py
"""

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "client" / "python"))

from playwright.async_api import async_playwright  # type: ignore
from game_auto import GameAuto

BASE_URL = os.environ.get("BASE_URL", "http://localhost:5173")
URL = f"{BASE_URL.rstrip('/')}/?demo&automation=1"

PRESETS = [
    "BRL",
    "USD",
    "EUR",
    "GBP",
    "INR",
    "RUB",
    "MXN",
    "ARS",
    "CLP",
    "COP",
    "PEN",
]


async def main() -> None:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=os.environ.get("HEADED") != "1")
        page = await browser.new_page(viewport={"width": 420, "height": 820})
        await page.goto(URL, wait_until="domcontentloaded")

        auto = GameAuto(page)
        await auto.wait_ready(timeout_ms=120_000)

        for code in PRESETS:
            result = await auto.set_currency(code)
            state = await auto.get_state()
            cur = state.get("currency") or {}
            print(
                f"{code}: code={cur.get('code')} symbol={cur.get('symbol')!r} "
                f"balance_fmt={state.get('balance_formatted')!r} "
                f"set_result_keys={list(result.keys()) if isinstance(result, dict) else result}"
            )
            assert str(cur.get("code", "")).upper() == code, (code, cur)

        print("OK — all presets applied")
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
