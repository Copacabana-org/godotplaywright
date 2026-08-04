// Abre o devplay em janela visível e tira screenshot do jogo.
//
//   node examples/devplay_shot.cjs                 # espera 20s, screenshot, fecha
//   WAIT=45000 node examples/devplay_shot.cjs      # pega uma fase mais tarde da rodada
//   KEEP=1 WAIT=900000 node examples/devplay_shot.cjs &   # deixa a janela aberta
//
// Variáveis: URL, WAIT (ms), KEEP (1 = não fecha), OUT (pasta dos png).
//
// game.png é o recorte do iframe do jogo — é ele que serve para comparar com o
// mockup. devplay.png é a janela inteira, com o painel de log.
const { chromium } = require('playwright')
const path = require('path')

const URL = process.env.URL || 'http://localhost:5173/devplay.html'
const WAIT = Number(process.env.WAIT || 20000)
const OUT = process.env.OUT || __dirname

;(async () => {
  const browser = await chromium.launch({
    headless: false, // sempre com janela: a ideia é o humano olhar junto
    args: ['--window-size=1500,1000', '--autoplay-policy=no-user-gesture-required'],
  })
  const page = await browser.newPage({ viewport: { width: 1500, height: 1000 } })
  page.on('console', (m) => console.log('[console]', m.text().slice(0, 200)))
  page.on('pageerror', (e) => console.log('[pageerror]', e.message))

  await page.goto(URL)
  await page.waitForTimeout(WAIT)

  await page.screenshot({ path: path.join(OUT, 'devplay.png') })
  await page.locator('#game').screenshot({ path: path.join(OUT, 'game.png') })
  console.log('log do bus:\n' + (await page.locator('#log').innerText()))

  if (process.env.KEEP) {
    // Mantém aberto: o processo só termina quando a janela fechar ou WAIT estourar.
    await page.waitForTimeout(WAIT).catch(() => {})
  }
  await browser.close().catch(() => {})
})()
