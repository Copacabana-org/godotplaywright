/**
 * Playwright (JS/TS) client for Godot Playwright.
 *
 * @example
 *   import { GameAuto } from './gameAuto.js'
 *   const auto = new GameAuto(page)
 *   await auto.waitReady()
 *   await auto.setLanguage('pt')
 *   await auto.betPlus(2)
 *   await auto.spin()
 *   await auto.waitTrack('spin_result')
 */

export class GameAuto {
  /**
   * @param {import('@playwright/test').Page} page
   */
  constructor(page) {
    this.page = page
  }

  async waitReady(timeoutMs = 90000) {
    await this.page.waitForFunction(
      () => window.__GAME_AUTO__ && window.__GAME_AUTO__.enabled,
      null,
      { timeout: timeoutMs },
    )
    await this.page.evaluate(async () => {
      await window.__GAME_AUTO__.ready
    })
  }

  /** @param {string} cmd @param {Record<string, any>} [args] */
  send(cmd, args = {}) {
    return this.page.evaluate(
      async ({ cmd, args }) => window.__GAME_AUTO__.send(cmd, args),
      { cmd, args },
    )
  }

  // ── pointer ──────────────────────────────────────────────────────────────

  move(x, y) {
    return this.page.evaluate(async ({ x, y }) => window.__GAME_AUTO__.move(x, y), { x, y })
  }

  mouseDown(x, y, button = 'left') {
    return this.page.evaluate(
      async ({ x, y, button }) => window.__GAME_AUTO__.mouseDown(x, y, button),
      { x, y, button },
    )
  }

  mouseUp(x, y, button = 'left') {
    return this.page.evaluate(
      async ({ x, y, button }) => window.__GAME_AUTO__.mouseUp(x, y, button),
      { x, y, button },
    )
  }

  click(x, y, button = 'left') {
    return this.page.evaluate(
      async ({ x, y, button }) => window.__GAME_AUTO__.click(x, y, button),
      { x, y, button },
    )
  }

  rightClick(x, y) {
    return this.click(x, y, 'right')
  }

  drag(x1, y1, x2, y2, steps = 10, button = 'left') {
    return this.page.evaluate(
      async ({ x1, y1, x2, y2, steps, button }) =>
        window.__GAME_AUTO__.drag(x1, y1, x2, y2, steps, button),
      { x1, y1, x2, y2, steps, button },
    )
  }

  tapControl(name) {
    return this.page.evaluate(async (name) => window.__GAME_AUTO__.tapControl(name), name)
  }

  getHotspots() {
    return this.page.evaluate(async () => window.__GAME_AUTO__.getHotspots())
  }

  // ── state ────────────────────────────────────────────────────────────────

  ping() {
    return this.page.evaluate(async () => window.__GAME_AUTO__.ping())
  }

  getState() {
    return this.page.evaluate(async () => window.__GAME_AUTO__.getState())
  }

  setCurrency(currencyOrPreset) {
    return this.page.evaluate(
      async (c) => window.__GAME_AUTO__.setCurrency(c),
      currencyOrPreset,
    )
  }

  /**
   * @param {string} eventName
   * @param {{ timeoutMs?: number }} [options]
   */
  waitTrack(eventName, options = {}) {
    const timeoutMs = options.timeoutMs ?? 30000
    return this.page.evaluate(
      async ({ eventName, timeoutMs }) =>
        window.__GAME_AUTO__.waitTrack(eventName, { timeoutMs }),
      { eventName, timeoutMs },
    )
  }

  // ── semantic (Template-line Godot shells) ────────────────────────────────

  setLanguage(code) {
    return this.page.evaluate(async (code) => window.__GAME_AUTO__.setLanguage(code), code)
  }

  openMenu() {
    return this.page.evaluate(async () => window.__GAME_AUTO__.openMenu())
  }

  openLanguages() {
    return this.page.evaluate(async () => window.__GAME_AUTO__.openLanguages())
  }

  openRules(viaMenu = false) {
    return this.page.evaluate(
      async (via_menu) => window.__GAME_AUTO__.openRules({ via_menu }),
      viaMenu,
    )
  }

  closeRules() {
    return this.page.evaluate(async () => window.__GAME_AUTO__.closeRules())
  }

  betPlus(times = 1) {
    return this.page.evaluate(async (times) => window.__GAME_AUTO__.betPlus(times), times)
  }

  betMinus(times = 1) {
    return this.page.evaluate(async (times) => window.__GAME_AUTO__.betMinus(times), times)
  }

  spin() {
    return this.page.evaluate(async () => window.__GAME_AUTO__.spin())
  }
}
