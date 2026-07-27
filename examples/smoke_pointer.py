"""
Smoke: pointer livre + ping + get_state.

  BASE_URL=https://staging-….example python smoke_pointer.py
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


async def main() -> None:
    print("URL:", URL)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=os.environ.get("HEADED") != "1")
        page = await browser.new_page(viewport={"width": 420, "height": 820})
        await page.goto(URL, wait_until="domcontentloaded", timeout=60_000)

        auto = GameAuto(page)
        await auto.wait_ready(timeout_ms=120_000)
        print("ping:", await auto.ping())
        print("state:", await auto.get_state())

        await auto.move(80, 120)
        await auto.click(200, 400)
        await auto.right_click(100, 100)
        await auto.drag(50, 500, 300, 500, steps=8)
        print("pointer OK")
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
