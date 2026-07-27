"""
Aplica presets de moeda e imprime balance formatado.

  BASE_URL=… python currency_matrix.py
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "client" / "python"))

from playwright.async_api import async_playwright  # type: ignore
from game_auto import GameAuto

BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:4173").rstrip("/")
URL = os.environ.get("GAME_URL", f"{BASE_URL}/?demo&automation=1")
PRESETS = ["BRL", "USD", "EUR", "CLP", "COP", "PEN"]


async def main() -> None:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=os.environ.get("HEADED") != "1")
        page = await browser.new_page(viewport={"width": 420, "height": 820})
        await page.goto(URL, wait_until="domcontentloaded")
        auto = GameAuto(page)
        await auto.wait_ready(timeout_ms=120_000)

        for code in PRESETS:
            await auto.set_currency(code)
            state = await auto.get_state()
            cur = state.get("currency") or {}
            print(f"{code}: {cur.get('symbol')!r}  {state.get('balance_formatted')!r}")
            assert str(cur.get("code", "")).upper() == code

        print("OK")
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
