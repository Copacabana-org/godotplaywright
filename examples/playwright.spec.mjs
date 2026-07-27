/**
 * Minimal @playwright/test example.
 *
 *   npm i -D @playwright/test
 *   npx playwright test examples/playwright.spec.mjs
 *
 * BASE_URL=https://staging-… npx playwright test
 */

import { test, expect } from '@playwright/test'
import { GameAuto } from '../client/js/gameAuto.js'

const BASE = process.env.BASE_URL || 'http://127.0.0.1:4173'

test('godotplaywright smoke', async ({ page }) => {
  await page.goto(`${BASE}/?demo&automation=1`)
  const auto = new GameAuto(page)
  await auto.waitReady(120_000)
  const pong = await auto.ping()
  expect(pong.pong).toBe(true)
  expect(pong.viewport).toBeTruthy()

  const state = await auto.getState()
  expect(state.protocol).toBe(1)
})
