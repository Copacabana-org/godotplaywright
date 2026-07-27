"""
Visible (headed) demo of Everest Game Auto — slow steps so a human can watch.

  HEADED=1 BASE_URL=http://127.0.0.1:4173 python demo_visible.py
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
URL = f"{BASE_URL}/?demo&automation=1"
PAUSE = float(os.environ.get("STEP_PAUSE", "1.8"))  # seconds between steps


async def pause(page, label: str) -> None:
    print(f"\n>>> {label}")
    # banner in-page so it's obvious on screen
    await page.evaluate(
        """(label) => {
      let el = document.getElementById('__auto_banner__');
      if (!el) {
        el = document.createElement('div');
        el.id = '__auto_banner__';
        el.style.cssText = 'position:fixed;top:8px;left:8px;right:8px;z-index:999999;'
          + 'background:rgba(0,0,0,.85);color:#0f0;font:14px/1.4 monospace;'
          + 'padding:10px 12px;border:1px solid #0f0;border-radius:8px;pointer-events:none';
        document.body.appendChild(el);
      }
      el.textContent = 'GAME AUTO: ' + label;
    }""",
        label,
    )
    await page.wait_for_timeout(int(PAUSE * 1000))


async def main() -> None:
    print(f"Opening visible browser → {URL}")
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=120,  # slow every CDP action a bit
            args=["--window-size=480,900", "--window-position=80,40"],
        )
        context = await browser.new_context(
            viewport={"width": 420, "height": 820},
            device_scale_factor=1,
        )
        page = await context.new_page()
        await page.goto(URL, wait_until="domcontentloaded", timeout=60_000)

        auto = GameAuto(page)
        await pause(page, "waiting for game + bridge…")
        await auto.wait_ready(timeout_ms=180_000)
        await pause(page, "READY — starting demo")

        pong = await auto.ping()
        await pause(page, f"ping ok — viewport {pong.get('viewport')}")

        state = await auto.get_state()
        await pause(
            page,
            f"state balance={state.get('balance_formatted')} bet={state.get('bet_formatted')}",
        )

        # free pointer path so motion is visible (move around then click)
        await pause(page, "MOVE mouse around (viewport coords)")
        for x, y in [(50, 80), (200, 200), (350, 400), (200, 800), (350, 1150)]:
            await auto.move(x, y)
            await page.wait_for_timeout(350)

        await pause(page, "LEFT CLICK near bottom bar (spin area)")
        await auto.click(350, 1200, "left")
        await page.wait_for_timeout(2500)

        await pause(page, "RIGHT CLICK top-left")
        await auto.right_click(80, 120)
        await page.wait_for_timeout(800)

        await pause(page, "DRAG horizontal")
        await auto.drag(80, 700, 340, 700, steps=16)
        await page.wait_for_timeout(800)

        # currency matrix — visible UI refresh
        for code in ["USD", "EUR", "CLP", "BRL"]:
            await pause(page, f"SET CURRENCY → {code}")
            await auto.set_currency(code)
            state = await auto.get_state()
            await pause(
                page,
                f"{code} formatted balance = {state.get('balance_formatted')}",
            )

        await pause(page, "DEMO DONE — window stays open 12s then closes")
        await page.wait_for_timeout(12_000)
        await browser.close()
        print("\nDone.")


if __name__ == "__main__":
    asyncio.run(main())
