"""
Playwright (Python) client for godotplaywright.

Usage:
    from game_auto import GameAuto

    async def test_flow(page):
        auto = GameAuto(page)
        await auto.wait_ready()
        await auto.set_language("pt")
        await auto.bet_plus(2)
        await auto.spin()
        await auto.wait_track("spin_result")
"""

from __future__ import annotations

from typing import Any, Optional


class GameAuto:
    def __init__(self, page: Any) -> None:
        self.page = page

    async def wait_ready(self, timeout_ms: int = 90_000) -> None:
        await self.page.wait_for_function(
            "() => window.__GAME_AUTO__ && window.__GAME_AUTO__.enabled",
            timeout=timeout_ms,
        )
        await self.page.evaluate("async () => { await window.__GAME_AUTO__.ready }")

    async def send(self, cmd: str, args: Optional[dict] = None) -> Any:
        return await self.page.evaluate(
            """async ({ cmd, args }) => window.__GAME_AUTO__.send(cmd, args || {})""",
            {"cmd": cmd, "args": args or {}},
        )

    async def move(self, x: float, y: float) -> Any:
        return await self.page.evaluate(
            """async ({ x, y }) => window.__GAME_AUTO__.move(x, y)""",
            {"x": x, "y": y},
        )

    async def mouse_down(self, x: float, y: float, button: str = "left") -> Any:
        return await self.page.evaluate(
            """async ({ x, y, button }) => window.__GAME_AUTO__.mouseDown(x, y, button)""",
            {"x": x, "y": y, "button": button},
        )

    async def mouse_up(self, x: float, y: float, button: str = "left") -> Any:
        return await self.page.evaluate(
            """async ({ x, y, button }) => window.__GAME_AUTO__.mouseUp(x, y, button)""",
            {"x": x, "y": y, "button": button},
        )

    async def click(self, x: float, y: float, button: str = "left") -> Any:
        return await self.page.evaluate(
            """async ({ x, y, button }) => window.__GAME_AUTO__.click(x, y, button)""",
            {"x": x, "y": y, "button": button},
        )

    async def right_click(self, x: float, y: float) -> Any:
        return await self.click(x, y, "right")

    async def drag(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        steps: int = 10,
        button: str = "left",
    ) -> Any:
        return await self.page.evaluate(
            """async ({ x1, y1, x2, y2, steps, button }) =>
                window.__GAME_AUTO__.drag(x1, y1, x2, y2, steps, button)""",
            {
                "x1": x1,
                "y1": y1,
                "x2": x2,
                "y2": y2,
                "steps": steps,
                "button": button,
            },
        )

    async def get_state(self) -> Any:
        return await self.page.evaluate("async () => window.__GAME_AUTO__.getState()")

    async def set_currency(self, currency_or_preset: Any) -> Any:
        return await self.page.evaluate(
            """async (c) => window.__GAME_AUTO__.setCurrency(c)""",
            currency_or_preset,
        )

    async def ping(self) -> Any:
        return await self.page.evaluate("async () => window.__GAME_AUTO__.ping()")

    async def get_hotspots(self) -> Any:
        return await self.page.evaluate("async () => window.__GAME_AUTO__.getHotspots()")

    async def tap_control(self, name: str) -> Any:
        return await self.page.evaluate(
            """async (name) => window.__GAME_AUTO__.tapControl(name)""",
            name,
        )

    async def set_language(self, code: str) -> Any:
        return await self.page.evaluate(
            """async (code) => window.__GAME_AUTO__.setLanguage(code)""",
            code,
        )

    async def open_menu(self) -> Any:
        return await self.page.evaluate("async () => window.__GAME_AUTO__.openMenu()")

    async def open_languages(self) -> Any:
        return await self.page.evaluate("async () => window.__GAME_AUTO__.openLanguages()")

    async def open_rules(self, via_menu: bool = False) -> Any:
        return await self.page.evaluate(
            """async (via_menu) => window.__GAME_AUTO__.openRules({ via_menu })""",
            via_menu,
        )

    async def close_rules(self) -> Any:
        return await self.page.evaluate("async () => window.__GAME_AUTO__.closeRules()")

    async def bet_plus(self, times: int = 1) -> Any:
        return await self.page.evaluate(
            """async (times) => window.__GAME_AUTO__.betPlus(times)""",
            times,
        )

    async def bet_minus(self, times: int = 1) -> Any:
        return await self.page.evaluate(
            """async (times) => window.__GAME_AUTO__.betMinus(times)""",
            times,
        )

    async def spin(self) -> Any:
        return await self.page.evaluate("async () => window.__GAME_AUTO__.spin()")

    async def wait_track(self, event_name: str, timeout_ms: int = 30_000) -> Any:
        return await self.page.evaluate(
            """async ({ eventName, timeoutMs }) =>
                window.__GAME_AUTO__.waitTrack(eventName, { timeoutMs })""",
            {"eventName": event_name, "timeoutMs": timeout_ms},
        )
