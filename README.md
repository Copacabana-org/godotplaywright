# godotplaywright

**Automação Playwright (JS/Python) para jogos Godot na web** — pensado para o padrão Everest (**Godot WASM + shell Vue**), reutilizável em jogos novos e antigos.

QA programa fluxos como qualquer e2e Playwright: **mover mouse, clicar L/R, drag, trocar moeda, idioma, abrir menu/regras, spin, esperar eventos**, sem depender de seletores DOM dentro do canvas.

```
Playwright (JS ou Python)
        │  page.evaluate → window.__GAME_AUTO__
        ▼
Vue shell  (GameAutoBridge.js)
        │  iframe.contentWindow.godotMessageReceiver(JSON)
        ▼
Godot autoload AutomationBridge
        │  push_input / activate buttons / semantic actions
        ▼
postMessage  auto_ready | auto_result | track
```

| Camada | Arquivo | Papel |
|--------|---------|--------|
| Godot | [`godot/automation_bridge.gd`](godot/automation_bridge.gd) | Autoload: input sintético + ações |
| Vue | [`vue/GameAutoBridge.js`](vue/GameAutoBridge.js) | `window.__GAME_AUTO__` no parent |
| Client JS | [`client/js/gameAuto.js`](client/js/gameAuto.js) | Helper Playwright JS/TS |
| Client Python | [`client/python/game_auto.py`](client/python/game_auto.py) | Helper Playwright Python |

---

## Quick start (QA com Playwright)

### Python

```bash
cd client/python
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

```python
from game_auto import GameAuto

async def test_smoke(page):
    await page.goto("https://staging-my-game.example/?automation=1")
    auto = GameAuto(page)
    await auto.wait_ready(timeout_ms=120_000)

    await auto.set_language("pt")
    await auto.bet_plus(2)
    await auto.spin()
    result = await auto.wait_track("spin_result", timeout_ms=30_000)
    assert result["event"] == "spin_result"

    state = await auto.get_state()
    print(state["balance_formatted"], state["currency"])
```

### JavaScript / TypeScript

```js
import { GameAuto } from '../client/js/gameAuto.js'

test('smoke', async ({ page }) => {
  await page.goto(process.env.BASE_URL + '/?automation=1')
  const auto = new GameAuto(page)
  await auto.waitReady()
  await auto.ping()
  await auto.setCurrency('USD')
  const state = await auto.getState()
  expect(state.currency.code).toBe('USD')
})
```

Também é possível chamar a API bruta sem o client:

```js
await page.evaluate(async () => {
  await window.__GAME_AUTO__.ready
  await window.__GAME_AUTO__.click(350, 1200)
})
```

---

## O que o bridge oferece

### Pointer (livre)

| Método | Descrição |
|--------|-----------|
| `move(x, y)` | Move no **viewport Godot** |
| `click(x, y, button?)` | Clique L/R (+ ativa `BaseButton` sob o ponto) |
| `rightClick(x, y)` | Atalho botão direito |
| `mouseDown` / `mouseUp` | Hold |
| `drag(x1,y1,x2,y2)` | Arraste |
| `getHotspots()` | Centros de controles conhecidos (PlusBtn, SpinBg, …) |
| `tapControl(name)` | Clica no centro de um nó por nome |

> Em Godot web, eventos de mouse sintéticos sozinhos costumam falhar em `TextureButton`. O bridge também **emite os signals** do botão sob o clique.

### Estado e observação

| Método | Descrição |
|--------|-----------|
| `ping()` | Healthcheck + viewport |
| `getState()` | balance, bet, currency, language, version… |
| `waitTrack(event)` | Espera `Tracker.track` do jogo (`spin_result`, …) |
| `setCurrency('USD'\|preset\|obj)` | Moeda em runtime (Template-line Helpers) |

### Ações semânticas (Everest Template-line)

Funcionam quando o jogo tem os nós/handlers padrão (`Portrait`, `SideMenu`, `Language`, `Rules`, …):

| Método | Descrição |
|--------|-----------|
| `setLanguage('pt')` | Painel de idioma ou Helpers |
| `openMenu()` | Abre sidebar |
| `openLanguages()` | Item Languages do menu |
| `openRules()` / `closeRules()` | Painel de regras |
| `betPlus(n)` / `betMinus(n)` | Altera aposta |
| `spin()` | Dispara spin |

Jogos com layout diferente podem estender `automation_bridge.gd` ou usar só pointer + `tapControl`.

---

## Integração no jogo (~15 min)

Guia completo: **[docs/INTEGRATION.md](docs/INTEGRATION.md)**  
Protocolo: **[docs/PROTOCOL.md](docs/PROTOCOL.md)**  
API de referência: **[docs/API.md](docs/API.md)**

### Resumo

1. Copie `godot/automation_bridge.gd` → autoload `AutomationBridge`
2. No `main.gd` (receiver JS), despache `action == "auto"` para `AutomationBridge.handle(data)`
3. Copie `vue/GameAutoBridge.js` e instale em `GamePage` se `isAutomationEnabled()`
4. Encaminhe `message` events para `gameAuto.handleParentMessage(event.data)`
5. Liste hosts de **produção** em `PROD_HOSTNAMES` (deny-list)
6. Reexporte Godot web + rebuild do shell

### Segurança

O bridge **só ativa** em:

- `localhost` / `127.0.0.1`
- hosts `staging-*`, `stag-*`, `dev-*`, `demo-*`
- **ou** `?automation=1` em host **não listado em prod**
- **ou** `localStorage.__GAME_AUTO__ = '1'`

Em produção (deny-list) permanece desligado.

---

## Estrutura do repositório

```
godotplaywright/
├── godot/automation_bridge.gd   # drop-in Godot
├── vue/GameAutoBridge.js        # drop-in Vue shell
├── client/
│   ├── js/gameAuto.js           # Playwright JS
│   └── python/game_auto.py      # Playwright Python
├── examples/                    # scripts de referência
├── docs/                        # integração, protocolo, API
└── README.md
```

Não inclui nenhum jogo (CrapsSlot, Gelato, …) — só o toolkit de QA.

---

## Exemplos

| Script | Uso |
|--------|-----|
| [`examples/smoke_pointer.py`](examples/smoke_pointer.py) | move / click / drag |
| [`examples/currency_matrix.py`](examples/currency_matrix.py) | todas as moedas preset |
| [`examples/playwright.spec.mjs`](examples/playwright.spec.mjs) | spec mínima `@playwright/test` |

```bash
export BASE_URL=https://staging-….casinoapp.live
python examples/smoke_pointer.py
```

---

## Requisitos

- Jogo Godot **4.x** exportado para **Web**, embutido em iframe same-origin no shell
- Shell com `godotMessageReceiver` (padrão Everest `broadcast`)
- Playwright recente (JS ou Python)
- Godot com `JavaScriptBridge` (export web)

---

## Contribuindo / versionamento

- Mudanças no **protocolo** (`cmd` novos) → documentar em `docs/PROTOCOL.md` e bumpar `PROTOCOL_VERSION` no GDScript.
- Preferir ações genéricas no bridge; lógica de um jogo só deve ficar no próprio jogo quando possível.

---

## Licença

MIT — ver [LICENSE](LICENSE).
