"""
Practical end-to-end test of Everest Game Auto against local Vite + exported Godot.

  BASE_URL=http://127.0.0.1:5173 \
  /path/to/venv/python practical_test.py

Exits 0 on success, 1 on failure. Writes screenshots under /tmp/game_auto_test/.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "client" / "python"))

from playwright.async_api import async_playwright  # type: ignore
from game_auto import GameAuto

BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:5173").rstrip("/")
URL = f"{BASE_URL}/?demo&automation=1"
OUT = Path(os.environ.get("OUT_DIR", "/tmp/game_auto_test"))
OUT.mkdir(parents=True, exist_ok=True)

# Failures collected; we try as many steps as possible.
failures: list[str] = []


def ok(msg: str) -> None:
    print(f"  ✓ {msg}")


def fail(msg: str) -> None:
    print(f"  ✗ {msg}")
    failures.append(msg)


async def main() -> int:
    print(f"URL: {URL}")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=os.environ.get("HEADED") != "1")
        context = await browser.new_context(
            viewport={"width": 420, "height": 820},
            device_scale_factor=1,
        )
        page = await context.new_page()

        # Capture console for debugging bridge issues
        logs: list[str] = []

        def on_console(msg):
            line = f"[{msg.type}] {msg.text}"
            logs.append(line)
            if msg.type in ("error", "warning") or "GAME_AUTO" in msg.text or "auto" in msg.text.lower():
                print(f"  console: {line[:200]}")

        page.on("console", on_console)
        page.on("pageerror", lambda e: print(f"  pageerror: {e}"))

        print("1) navigate")
        await page.goto(URL, wait_until="domcontentloaded", timeout=60_000)
        await page.screenshot(path=str(OUT / "01_navigate.png"))
        ok(f"loaded, title={await page.title()!r}")

        print("2) wait for window.__GAME_AUTO__")
        try:
            await page.wait_for_function(
                "() => window.__GAME_AUTO__ && window.__GAME_AUTO__.enabled",
                timeout=30_000,
            )
            ok("__GAME_AUTO__ enabled")
        except Exception as e:
            fail(f"__GAME_AUTO__ never appeared: {e}")
            await page.screenshot(path=str(OUT / "02_no_bridge.png"))
            # dump what's on the page
            html = await page.content()
            (OUT / "page.html").write_text(html[:50000])
            print("  first 30 console lines:")
            for l in logs[:30]:
                print("   ", l[:180])
            await browser.close()
            return 1

        print("3) wait for bridge ready (game_loaded + auto_ready)…")
        auto = GameAuto(page)
        try:
            await auto.wait_ready(timeout_ms=180_000)
            ok("ready")
        except Exception as e:
            fail(f"wait_ready failed: {e}")
            # Diagnostic: what's the shell state?
            diag = await page.evaluate(
                """() => ({
                  hasAuto: !!window.__GAME_AUTO__,
                  demo: !!window.__DEMO_MODE__,
                  flag: localStorage.getItem('__GAME_AUTO__'),
                  game_id: localStorage.getItem('game_id'),
                  iframes: [...document.querySelectorAll('iframe')].map(f => ({
                    src: f.src, hidden: f.offsetParent === null, w: f.offsetWidth, h: f.offsetHeight
                  })),
                })"""
            )
            print("  diag:", json.dumps(diag, indent=2))
            await page.screenshot(path=str(OUT / "03_not_ready.png"))
            (OUT / "console.txt").write_text("\n".join(logs))
            # Continue anyway if possible — try ping
        else:
            await page.screenshot(path=str(OUT / "03_ready.png"))

        print("4) ping")
        try:
            pong = await auto.ping()
            print("  ping →", pong)
            if not pong.get("pong"):
                fail(f"ping missing pong: {pong}")
            else:
                ok(f"ping protocol={pong.get('protocol')} viewport={pong.get('viewport')}")
        except Exception as e:
            fail(f"ping failed: {e}")
            traceback.print_exc()
            await page.screenshot(path=str(OUT / "04_ping_fail.png"))
            (OUT / "console.txt").write_text("\n".join(logs))
            await browser.close()
            return 1

        print("5) get_state")
        try:
            state = await auto.get_state()
            print("  state →", json.dumps(state, indent=2)[:800])
            if "viewport" not in state:
                fail("get_state missing viewport")
            else:
                ok(f"viewport={state['viewport']} currency={state.get('currency')}")
            (OUT / "state.json").write_text(json.dumps(state, indent=2))
        except Exception as e:
            fail(f"get_state failed: {e}")

        print("6) free pointer: move + left click + right click")
        try:
            await auto.move(80, 120)
            await auto.move(200, 400)
            r = await auto.click(350, 1100, "left")
            print("  click →", r)
            r2 = await auto.right_click(100, 150)
            print("  right_click →", r2)
            ok("pointer commands returned ok")
            await page.wait_for_timeout(500)
            await page.screenshot(path=str(OUT / "06_after_pointer.png"))
        except Exception as e:
            fail(f"pointer failed: {e}")
            traceback.print_exc()

        print("7) currency matrix (BRL → USD → EUR → CLP → BRL)")
        for code in ["BRL", "USD", "EUR", "CLP", "BRL"]:
            try:
                result = await auto.set_currency(code)
                state = await auto.get_state()
                cur = (state or {}).get("currency") or {}
                got = str(cur.get("code", "")).upper()
                fmt = state.get("balance_formatted")
                print(f"  {code}: code={got} symbol={cur.get('symbol')!r} balance_fmt={fmt!r}")
                if got != code:
                    fail(f"set_currency {code}: got {got}")
                else:
                    ok(f"{code} → {fmt}")
                await page.screenshot(path=str(OUT / f"07_currency_{code}.png"))
            except Exception as e:
                fail(f"set_currency {code}: {e}")
                traceback.print_exc()

        print("8) drag")
        try:
            r = await auto.drag(100, 600, 300, 600, steps=8)
            print("  drag →", r)
            ok("drag ok")
        except Exception as e:
            fail(f"drag failed: {e}")

        await page.screenshot(path=str(OUT / "99_final.png"))
        (OUT / "console.txt").write_text("\n".join(logs))
        await browser.close()

    print()
    if failures:
        print(f"FAILED ({len(failures)}):")
        for f in failures:
            print(" -", f)
        print(f"Artifacts: {OUT}")
        return 1
    print(f"ALL PASSED. Artifacts: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
