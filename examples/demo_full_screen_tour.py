"""
Full UI tour with screenshots — modals closed correctly between steps.

  BASE_URL=http://127.0.0.1:4174 OUT_DIR=/tmp/godot_tour \
    python demo_full_screen_tour.py
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "client" / "python"))

from playwright.async_api import async_playwright  # type: ignore
from game_auto import GameAuto

BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:4174").rstrip("/")
URL = f"{BASE_URL}/?demo&automation=1"
OUT = Path(os.environ.get("OUT_DIR", "/tmp/godot_tour"))
HEADED = os.environ.get("HEADED", "1") != "0"
PAUSE = float(os.environ.get("STEP_PAUSE", "1.0"))
BURST_INTERVAL_MS = int(os.environ.get("BURST_MS", "280"))
SPIN_BURST_N = int(os.environ.get("SPIN_BURST_N", "16"))

seq = 0
manifest: list[dict] = []


async def banner(page, text: str) -> None:
    print(f"\n>>> {text}")
    await page.evaluate(
        """(text) => {
      let el = document.getElementById('__auto_banner__');
      if (!el) {
        el = document.createElement('div');
        el.id = '__auto_banner__';
        el.style.cssText = 'position:fixed;top:6px;left:6px;right:6px;z-index:999999;'
          + 'background:rgba(0,0,0,.88);color:#0f0;font:13px/1.35 monospace;'
          + 'padding:10px 12px;border:1px solid #0f0;border-radius:8px;pointer-events:none';
        document.body.appendChild(el);
      }
      el.style.display = 'block';
      el.textContent = 'TOUR: ' + text;
    }""",
        text,
    )
    await page.wait_for_timeout(int(PAUSE * 1000))


async def hide_banner(page) -> None:
    await page.evaluate(
        """() => {
      const el = document.getElementById('__auto_banner__');
      if (el) el.style.display = 'none';
    }"""
    )


async def show_banner(page) -> None:
    await page.evaluate(
        """() => {
      const el = document.getElementById('__auto_banner__');
      if (el) el.style.display = 'block';
    }"""
    )


async def shot(page, label: str) -> Path:
    global seq
    seq += 1
    name = f"{seq:03d}_{label}"
    await hide_banner(page)
    await page.wait_for_timeout(80)
    path = OUT / f"{name}.png"
    await page.screenshot(path=str(path), full_page=False)
    iframe_path = None
    for f in page.frames:
        u = f.url or ""
        if "loader" in u:
            continue
        if "godot" in u or "game.html" in u or u.endswith("/index.html"):
            try:
                el = await f.frame_element()
                iframe_path = OUT / f"{name}_game.png"
                await el.screenshot(path=str(iframe_path))
            except Exception:
                pass
            break
    await show_banner(page)
    manifest.append(
        {
            "n": seq,
            "label": label,
            "page": str(path),
            "game": str(iframe_path) if iframe_path else None,
        }
    )
    print(f"  📸 {path.name}" + (f" + {iframe_path.name}" if iframe_path else ""))
    return path


async def burst(page, label_prefix: str, n: int, interval_ms: int) -> None:
    for i in range(n):
        await shot(page, f"{label_prefix}_{i:02d}")
        if i < n - 1:
            await page.wait_for_timeout(interval_ms)


async def safe(coro, what: str):
    try:
        return await coro
    except Exception as e:
        print(f"  ! {what}: {e}")
        return None


async def clear_ui(auto: GameAuto) -> None:
    """Always return to a clean main-game surface."""
    r = await safe(auto.close_overlays(), "close_overlays")
    print("  close_overlays →", r)
    await asyncio.sleep(0.35)


async def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    # wipe previous run
    for p in OUT.glob("*.png"):
        p.unlink()
    print(f"URL={URL}\nOUT={OUT}\nHEADED={HEADED}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=not HEADED,
            slow_mo=30 if HEADED else 0,
            args=["--window-size=480,920", "--window-position=40,20"],
        )
        page = await browser.new_page(viewport={"width": 420, "height": 820})

        await page.goto(URL, wait_until="domcontentloaded", timeout=90_000)
        await page.evaluate(
            """() => {
              localStorage.removeItem('language');
              localStorage.setItem('__GAME_AUTO__', '1');
            }"""
        )
        await page.reload(wait_until="domcontentloaded")
        await shot(page, "00_navigate_shell")

        auto = GameAuto(page)
        await banner(page, "waiting game + bridge…")
        for i in range(5):
            await shot(page, f"01_loading_{i:02d}")
            try:
                if await page.evaluate(
                    "() => !!(window.__GAME_AUTO__ && window.__GAME_AUTO__.enabled)"
                ):
                    break
            except Exception:
                pass
            await page.wait_for_timeout(1200)

        await auto.wait_ready(timeout_ms=180_000)
        await banner(page, "READY")
        await shot(page, "02_ready")

        # Language first-run
        await banner(page, "language panel")
        await shot(page, "03_language_panel")
        await banner(page, "select Português")
        await safe(auto.set_language("pt"), "set_language pt")
        await burst(page, "04_lang_pt_transition", 4, 200)
        await clear_ui(auto)
        await shot(page, "05_main_after_lang")

        await banner(page, "main idle")
        await shot(page, "06_main_idle")

        # Menu
        await banner(page, "open MENU")
        await safe(auto.open_menu(), "open_menu")
        await burst(page, "07_menu_open", 4, 180)
        await shot(page, "08_menu_open")
        await clear_ui(auto)
        await shot(page, "09_main_after_menu")

        # History
        await banner(page, "open HISTORY")
        await safe(auto.open_history(via_menu=True), "open_history")
        await burst(page, "10_history_open", 4, 200)
        await shot(page, "11_history")
        await banner(page, "close HISTORY")
        await safe(auto.close_history(), "close_history")
        await page.wait_for_timeout(400)
        await clear_ui(auto)
        await shot(page, "12_main_after_history")

        # Rules
        await banner(page, "open RULES")
        await safe(auto.open_rules(via_menu=True), "open_rules")
        await burst(page, "13_rules_open", 4, 200)
        await shot(page, "14_rules_pt")
        await banner(page, "close RULES")
        await safe(auto.close_rules(), "close_rules")
        await clear_ui(auto)
        await shot(page, "15_main_after_rules")

        # Languages via menu → EN
        await banner(page, "MENU → Languages → EN")
        await safe(auto.open_menu(), "open_menu")
        await page.wait_for_timeout(600)
        await safe(auto.open_languages(), "open_languages")
        await burst(page, "16_languages_panel", 3, 200)
        await shot(page, "17_languages_panel")
        await safe(auto.set_language("en"), "set_language en")
        await burst(page, "18_lang_en_transition", 4, 200)
        await clear_ui(auto)
        await shot(page, "19_main_en")

        # Currency (clean main)
        for code in ["USD", "EUR", "BRL"]:
            await banner(page, f"currency → {code}")
            await clear_ui(auto)
            await safe(auto.set_currency(code), f"currency {code}")
            await page.wait_for_timeout(350)
            await shot(page, f"20_currency_{code}")

        # Autoplay
        await banner(page, "open AUTOPLAY")
        await clear_ui(auto)
        spots = await safe(auto.get_hotspots(), "hotspots") or {}
        auto_hs = next(
            (h for h in (spots.get("hotspots") or []) if h.get("name") == "AutoBtn"),
            None,
        )
        if auto_hs:
            await safe(auto.click(auto_hs["x"], auto_hs["y"]), "click AutoBtn")
        else:
            await safe(auto.tap_control("AutoBtn"), "tap AutoBtn")
        await burst(page, "21_autoplay_open", 4, 200)
        await shot(page, "22_autoplay_panel")
        await clear_ui(auto)
        # Extra dismiss click if panel still open
        await safe(auto.click(50, 50), "dismiss click")
        await page.wait_for_timeout(300)
        await clear_ui(auto)
        await shot(page, "23_main_after_autoplay")

        # Bet +
        await banner(page, "bet + x4")
        await clear_ui(auto)
        await safe(auto.bet_plus(4), "bet_plus")
        await burst(page, "24_bet_plus", 3, 150)
        st = await safe(auto.get_state(), "state")
        await shot(page, f"25_bet_{(st or {}).get('current_bet', 'x')}")

        # Spin with animation burst — must be on clean main
        await banner(page, "SPIN — animation frames")
        await clear_ui(auto)
        await shot(page, "26_pre_spin")
        spin_task = asyncio.create_task(safe(auto.spin(), "spin"))
        await page.wait_for_timeout(80)
        await burst(page, "27_spin_anim", SPIN_BURST_N, BURST_INTERVAL_MS)
        await spin_task
        try:
            ev = await auto.wait_track("spin_result", timeout_ms=25_000)
            print("  spin_result", ev)
            await shot(page, "28_spin_result")
            await burst(page, "29_post_spin", 8, 280)
        except Exception as e:
            print("  wait_track:", e)
            await burst(page, "29_post_spin", 5, 280)

        await clear_ui(auto)
        await shot(page, "30_final")

        # Validation: final must NOT contain stuck History title in page shot name check
        # (manual review of 30_final_game.png)

        lines = [
            "# Full screen tour (fixed close)",
            "",
            f"frames: **{seq}**",
            "",
        ]
        for m in manifest:
            lines.append(f"### {m['n']:03d} — `{m['label']}`")
            lines.append(f"![{m['label']}]({Path(m['page']).name})")
            lines.append("")
        (OUT / "index.md").write_text("\n".join(lines))
        (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2))
        print(f"\nDone — {seq} shots in {OUT}")

        await banner(page, f"DONE — {seq} shots")
        await page.wait_for_timeout(5000)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
