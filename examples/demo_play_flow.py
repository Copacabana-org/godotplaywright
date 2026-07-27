"""
Visible demo: Portuguese → increase bet → spin.

Uses reliable game actions (set_language / bet_plus / spin) because pure
synthetic mouse events often miss TextureButtons on Godot web.

  BASE_URL=http://127.0.0.1:4173 python demo_play_flow.py
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
PAUSE = float(os.environ.get("STEP_PAUSE", "2.5"))


async def banner(page, text: str) -> None:
    print(f"\n>>> {text}")
    await page.evaluate(
        """(text) => {
      let el = document.getElementById('__auto_banner__');
      if (!el) {
        el = document.createElement('div');
        el.id = '__auto_banner__';
        el.style.cssText = 'position:fixed;top:8px;left:8px;right:8px;z-index:999999;'
          + 'background:rgba(0,0,0,.88);color:#0f0;font:15px/1.4 monospace;'
          + 'padding:12px 14px;border:2px solid #0f0;border-radius:8px;pointer-events:none';
        document.body.appendChild(el);
      }
      el.textContent = 'GAME AUTO: ' + text;
    }""",
        text,
    )
    await page.wait_for_timeout(int(PAUSE * 1000))


async def main() -> None:
    print(f"Opening browser → {URL}")
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=80,
            args=["--window-size=480,920", "--window-position=60,30"],
        )
        page = await browser.new_page(viewport={"width": 420, "height": 820})
        # Fresh language so the picker is meaningful (clear prior choice).
        await page.goto(URL, wait_until="domcontentloaded", timeout=60_000)
        await page.evaluate(
            """() => {
              localStorage.removeItem('language');
              // keep automation flag
              localStorage.setItem('__GAME_AUTO__', '1');
            }"""
        )
        # Reload so language panel opens without saved preference
        await page.reload(wait_until="domcontentloaded")

        auto = GameAuto(page)
        await banner(page, "waiting for game…")
        await auto.wait_ready(timeout_ms=180_000)
        await banner(page, "READY")

        hotspots = await auto.get_hotspots()
        print("hotspots:", hotspots)

        # 1) Portuguese
        await banner(page, "selecting language: Português (pt)")
        r = await auto.set_language("pt")
        print("set_language →", r)
        state = await auto.get_state()
        await banner(page, f"language done — locale={state.get('language')}")
        await page.wait_for_timeout(1500)

        # 2) Increase bet a few times (visible on Aposta label)
        await banner(page, "bet +  (3x)")
        before = (await auto.get_state()).get("bet_formatted")
        r = await auto.bet_plus(3)
        print("bet_plus →", r)
        after = (await auto.get_state()).get("bet_formatted")
        await banner(page, f"bet: {before} → {after}")
        await page.wait_for_timeout(1000)

        # Also show hotspot click path for PlusBtn (pointer + activate)
        spots = (await auto.get_hotspots()).get("hotspots") or []
        plus = next((h for h in spots if h.get("name") == "PlusBtn"), None)
        if plus:
            await banner(page, f"also CLICK PlusBtn at ({plus['x']:.0f},{plus['y']:.0f})")
            r = await auto.click(plus["x"], plus["y"])
            print("click PlusBtn →", r)
            await banner(page, f"bet now {(await auto.get_state()).get('bet_formatted')}")

        # 3) Spin
        await banner(page, "SPIN!")
        r = await auto.spin()
        print("spin →", r)
        await banner(page, "spin started — watching reels…")
        # Wait for gameplay telemetry if any
        try:
            ev = await auto.wait_track("spin_result", timeout_ms=45_000)
            print("spin_result →", ev)
            await banner(page, f"spin_result received: {ev.get('event')}")
        except Exception as e:
            print("wait_track spin_result:", e)
            await banner(page, "no spin_result track (may still animate)")

        await banner(page, "DONE — window open 15s")
        await page.wait_for_timeout(15_000)
        await browser.close()
        print("\nDone.")


if __name__ == "__main__":
    asyncio.run(main())
