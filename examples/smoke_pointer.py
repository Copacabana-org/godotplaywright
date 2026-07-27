"""
Free pointer scripting example (no game-specific actions).

  BASE_URL=https://staging-craps-slot.casinoapp.live \
    python smoke_pointer.py

Coords are Godot viewport space (see get_state()["viewport"]).
"""

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "client" / "python"))

from playwright.async_api import async_playwright  # type: ignore
from game_auto import GameAuto


BASE_URL = os.environ.get("BASE_URL", "http://localhost:5173")
# Always request automation; shell only enables on non-prod hosts.
URL = f"{BASE_URL.rstrip('/')}/?demo&automation=1"


async def main() -> None:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=os.environ.get("HEADED") != "1")
        page = await browser.new_page(viewport={"width": 420, "height": 820})
        await page.goto(URL, wait_until="domcontentloaded")

        auto = GameAuto(page)
        print("waiting for game auto bridge…")
        await auto.wait_ready(timeout_ms=120_000)

        pong = await auto.ping()
        print("ping:", pong)

        state = await auto.get_state()
        print("viewport:", state.get("viewport"))
        print("currency:", state.get("currency"))

        # Free form: move around and click anywhere — QA scripts whatever they need.
        await auto.move(50, 50)
        await auto.move(200, 400)
        await auto.click(350, 1200)  # often near bottom bar on 700x1370 slots
        await auto.right_click(100, 100)

        # Optional: wait for a gameplay track event if a click started something.
        # try:
        #     ev = await auto.wait_track("spin_result", timeout_ms=30_000)
        #     print("track:", ev)
        # except Exception as e:
        #     print("no spin_result (ok if click missed spin):", e)

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
