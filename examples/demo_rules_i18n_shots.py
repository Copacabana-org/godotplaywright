"""
Visible demo + screenshots: Rules screen for the first N languages.

Default langs (first 5 in game LANGUAGES list): pt, en, es, hi, ru

  BASE_URL=http://127.0.0.1:4174 \
  OUT_DIR=/tmp/rules_i18n \
  STEP_PAUSE=2.5 \
  python demo_rules_i18n_shots.py

Env:
  LANGS=pt,en,es,hi,ru   override language list
  OUT_DIR=...            screenshot folder
  STEP_PAUSE=2.5         seconds between steps (recording)
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "client" / "python"))

from playwright.async_api import async_playwright  # type: ignore
from game_auto import GameAuto

BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:4174").rstrip("/")
URL = f"{BASE_URL}/?demo&automation=1"
PAUSE = float(os.environ.get("STEP_PAUSE", "2.5"))
OUT = Path(os.environ.get("OUT_DIR", "/tmp/rules_i18n"))
# First 5 languages from Godot language.gd LANGUAGES order
DEFAULT_LANGS = ["pt", "en", "es", "hi", "ru"]
LANGS = [
    x.strip()
    for x in os.environ.get("LANGS", ",".join(DEFAULT_LANGS)).split(",")
    if x.strip()
]


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


async def hide_banner(page) -> None:
    """Hide banner for clean screenshots of rules content."""
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


async def shot(page, name: str) -> Path:
    await hide_banner(page)
    await page.wait_for_timeout(200)
    path = OUT / f"{name}.png"
    # Full page (includes shell + game iframe)
    await page.screenshot(path=str(path), full_page=False)
    # Also try iframe-only if present (crisper game UI)
    frames = page.frames
    game_frame = None
    for f in frames:
        if f.url and ("godot" in f.url or "game.html" in f.url or "index.html" in f.url):
            if "loader" not in f.url:
                game_frame = f
                break
    if game_frame:
        try:
            el = await game_frame.frame_element()
            iframe_path = OUT / f"{name}_iframe.png"
            await el.screenshot(path=str(iframe_path))
            print(f"  📸 {iframe_path}")
        except Exception as e:
            print(f"  (iframe shot skip: {e})")
    await show_banner(page)
    print(f"  📸 {path}")
    return path


async def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"URL: {URL}")
    print(f"langs: {LANGS}")
    print(f"OUT: {OUT}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=60,
            args=["--window-size=480,920", "--window-position=60,30"],
        )
        page = await browser.new_page(viewport={"width": 420, "height": 820})
        await page.goto(URL, wait_until="domcontentloaded", timeout=60_000)
        await page.evaluate(
            """() => {
              localStorage.removeItem('language');
              localStorage.setItem('__GAME_AUTO__', '1');
            }"""
        )
        await page.reload(wait_until="domcontentloaded")

        auto = GameAuto(page)
        await banner(page, "waiting for game…")
        await auto.wait_ready(timeout_ms=180_000)
        await banner(page, f"READY — rules i18n shots ({len(LANGS)} langs)")

        # Dismiss first-run language panel with first lang so game is usable
        first = LANGS[0]
        await banner(page, f"bootstrap locale → {first}")
        await auto.set_language(first)
        await page.wait_for_timeout(800)

        for i, code in enumerate(LANGS, start=1):
            await banner(page, f"[{i}/{len(LANGS)}] language → {code}")
            r = await auto.set_language(code)
            print("  set_language →", r)
            await page.wait_for_timeout(600)

            await banner(page, f"[{i}/{len(LANGS)}] open RULES ({code})")
            # via_menu=false is enough; direct SideBar handler / Rules._show
            r = await auto.open_rules(via_menu=True)
            print("  open_rules →", r)
            # Let panel animate + translations apply
            await page.wait_for_timeout(1200)

            await banner(page, f"[{i}/{len(LANGS)}] screenshot rules_{code}")
            await shot(page, f"rules_{i:02d}_{code}")

            await banner(page, f"[{i}/{len(LANGS)}] close rules")
            r = await auto.close_rules()
            print("  close_rules →", r)
            await page.wait_for_timeout(700)

        # Index file for QA
        index = OUT / "index.md"
        lines = [
            "# Rules i18n screenshots",
            "",
            f"langs: {', '.join(LANGS)}",
            "",
        ]
        for i, code in enumerate(LANGS, start=1):
            lines.append(f"## {code}")
            lines.append(f"![rules_{code}](rules_{i:02d}_{code}.png)")
            lines.append("")
        index.write_text("\n".join(lines))
        print(f"\nIndex: {index}")

        await banner(page, "DONE — window open 12s (stop recording)")
        await page.wait_for_timeout(12_000)
        await browser.close()
        print("\nAll screenshots in", OUT)


if __name__ == "__main__":
    asyncio.run(main())
