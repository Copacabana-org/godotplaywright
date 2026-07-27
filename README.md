# godotplaywright

**Automação Playwright (JS / Python) para jogos Godot na web.**

Feito para o padrão Everest (**Godot WASM + shell Vue** em iframe), reutilizável em jogos **novos e antigos**. O QA programa fluxos como qualquer e2e Playwright — **sem seletores DOM dentro do canvas**.

```
Playwright (JS ou Python)
        │  page.evaluate → window.__GAME_AUTO__
        ▼
Vue shell  (GameAutoBridge.js)
        │  iframe.contentWindow.godotMessageReceiver(JSON)
        ▼
Godot autoload AutomationBridge
        │  push_input · activate buttons · semantic actions
        ▼
postMessage  auto_ready | auto_result | track
```

| Camada | Path | Papel |
|--------|------|--------|
| Godot | [`godot/automation_bridge.gd`](godot/automation_bridge.gd) | Autoload: input + ações |
| Vue | [`vue/GameAutoBridge.js`](vue/GameAutoBridge.js) | `window.__GAME_AUTO__` no parent |
| Client JS | [`client/js/gameAuto.js`](client/js/gameAuto.js) | Helper `@playwright/test` |
| Client Python | [`client/python/game_auto.py`](client/python/game_auto.py) | Helper Playwright Python |

**Docs**

| Doc | Conteúdo |
|-----|----------|
| [docs/INTEGRATION.md](docs/INTEGRATION.md) | Como plugar no jogo (Godot + Vue) — checklist de PR |
| [docs/API.md](docs/API.md) | API dos clients JS/Python |
| [docs/PROTOCOL.md](docs/PROTOCOL.md) | Envelope de mensagens (para implementadores) |
| [examples/](examples/) | Scripts de demo / smoke |

---

## Para quem já usa Playwright

Se você já escreve e2e, isto é um **page object** do jogo:

```python
from game_auto import GameAuto

async def test_smoke(page):
    await page.goto("https://staging-my-game.example/?automation=1")
    auto = GameAuto(page)
    await auto.wait_ready(timeout_ms=120_000)

    await auto.set_language("pt")
    await auto.open_menu()
    await auto.open_rules(via_menu=True)
    await auto.close_rules()

    await auto.bet_plus(2)
    await auto.spin()
    result = await auto.wait_track("spin_result", timeout_ms=30_000)
    assert result["event"] == "spin_result"

    state = await auto.get_state()
    assert "balance" in state
```

```js
import { GameAuto } from '../client/js/gameAuto.js'

test('smoke', async ({ page }) => {
  await page.goto(process.env.BASE_URL + '/?automation=1')
  const auto = new GameAuto(page)
  await auto.waitReady()
  await auto.setLanguage('pt')
  await auto.betPlus(2)
  await auto.spin()
  await auto.waitTrack('spin_result', { timeoutMs: 30_000 })
})
```

Sem o client, a API bruta no browser:

```js
await page.evaluate(async () => {
  await window.__GAME_AUTO__.ready
  await window.__GAME_AUTO__.click(350, 1200)
  await window.__GAME_AUTO__.setCurrency('USD')
})
```

---

## Quick start — client de QA

### Python

```bash
git clone https://github.com/Copacabana-org/godotplaywright.git
cd godotplaywright/client/python
python -m venv .venv && source .venv/bin/activate   # ou fish: source .venv/bin/activate.fish
pip install -r requirements.txt
playwright install chromium
```

```python
# no seu teste — adicione client/python ao PYTHONPATH ou copie o arquivo
from game_auto import GameAuto
```

### JavaScript / TypeScript

```bash
# no repo de e2e do jogo:
cp path/to/godotplaywright/client/js/gameAuto.js  e2e/helpers/gameAuto.js
```

```js
import { GameAuto } from './helpers/gameAuto.js'
```

### URL de teste

| Ambiente | Como ligar o bridge |
|----------|---------------------|
| Staging / dev / demo hosts | liga sozinho **ou** `?automation=1` |
| localhost | liga sozinho |
| Production (`PROD_HOSTNAMES`) | **nunca** |
| Demo offline | `?demo&automation=1` no **build** (`vite preview`), não no `vite dev` |

---

## O que o QA consegue fazer

### Pointer livre (qualquer jogo com o bridge)

| Ação | Python | JS |
|------|--------|-----|
| Mover | `move(x, y)` | `move(x, y)` |
| Clique L/R | `click` / `right_click` | `click` / `rightClick` |
| Hold | `mouse_down` / `mouse_up` | `mouseDown` / `mouseUp` |
| Drag | `drag(x1,y1,x2,y2)` | `drag(...)` |
| Por nome de nó | `tap_control("PlusBtn")` | `tapControl("PlusBtn")` |
| Listar alvos | `get_hotspots()` | `getHotspots()` |

Coordenadas = **viewport Godot** (ex. 700×1370), não pixels CSS. Use `get_state()["viewport"]`.

### Estado e asserts

| Ação | Método |
|------|--------|
| Healthcheck | `ping()` |
| Snapshot | `get_state()` → balance, bet, currency, language, version |
| Moeda runtime | `set_currency("USD")` (sem remount) |
| Evento de gameplay | `wait_track("spin_result")` (reusa `Tracker.track`) |

### Semântica Template-line (slots Everest com SideMenu / Portrait)

| Ação | Método |
|------|--------|
| Idioma | `set_language("pt")` |
| Menu | `open_menu()` |
| Idiomas no menu | `open_languages()` |
| Regras | `open_rules()` / `close_rules()` |
| Histórico | `open_history()` / `close_history()` |
| Limpar tudo | `close_overlays()` ← **use entre passos de tour** |
| Aposta | `bet_plus(n)` / `bet_minus(n)` |
| Spin | `spin()` |

Se o jogo não tiver esses nós, o cmd retorna erro tipado — use pointer + hotspots.

> **Overlay escuro:** fechar só o modal não basta. Chame `close_overlays()` (limpa `MenuDimmer` + `SideMenu/Overlay` + sidebar).

---

## Integrar em um jogo (dev)

Resumo — detalhes em **[docs/INTEGRATION.md](docs/INTEGRATION.md)**:

1. **Godot:** copiar `automation_bridge.gd` → autoload `AutomationBridge` → despachar `action == "auto"` no `godotMessageReceiver`.
2. **Vue:** copiar `GameAutoBridge.js` → `installGameAutoBridge` no GamePage → `handleParentMessage` no `message` listener.
3. Preencher **`PROD_HOSTNAMES`** com o host de produção do jogo.
4. Reexport web + rebuild shell.
5. Smoke: `ping` + `getState` em staging/`?automation=1`.

Tempo típico: **~15 min** no primeiro jogo; os seguintes são copy-paste.

---

## Exemplos

| Script | O que faz |
|--------|-----------|
| [`examples/smoke_pointer.py`](examples/smoke_pointer.py) | ping + move/click |
| [`examples/currency_matrix.py`](examples/currency_matrix.py) | todas as moedas preset |
| [`examples/demo_play_flow.py`](examples/demo_play_flow.py) | pt → bet+ → spin (headed) |
| [`examples/demo_menu_lang_spin.py`](examples/demo_menu_lang_spin.py) | pt → menu → muda idioma → bet → spin |
| [`examples/demo_rules_i18n_shots.py`](examples/demo_rules_i18n_shots.py) | regras nas 5 primeiras línguas + PNG |
| [`examples/demo_full_screen_tour.py`](examples/demo_full_screen_tour.py) | tour completo + animações + PNGs |
| [`examples/playwright.spec.mjs`](examples/playwright.spec.mjs) | esqueleto `@playwright/test` |

```bash
export BASE_URL=https://staging-my-game.example   # ou http://127.0.0.1:4174
cd examples
# headed (para gravar / demo)
python demo_play_flow.py
# screenshots de regras
OUT_DIR=/tmp/rules_i18n LANGS=pt,en,es,hi,ru python demo_rules_i18n_shots.py
# tour visual completo (saída em /tmp/godot_tour)
OUT_DIR=/tmp/godot_tour python demo_full_screen_tour.py
```

---

## Segurança

- Bridge **só** em hosts não-prod (ou `?automation=1` fora da deny-list).
- Em produção listada em `PROD_HOSTNAMES`, `window.__GAME_AUTO__` **não** é instalado.
- Flag Godot: `localStorage.__GAME_AUTO__ = "1"` setada pelo shell **antes** do iframe do jogo carregar.

---

## Estrutura do repositório

```
godotplaywright/
├── godot/automation_bridge.gd     # drop-in autoload
├── vue/GameAutoBridge.js          # drop-in shell bridge
├── client/
│   ├── js/gameAuto.js
│   └── python/game_auto.py
├── docs/
│   ├── INTEGRATION.md
│   ├── API.md
│   └── PROTOCOL.md
├── examples/
└── README.md
```

Não inclui assets de jogo, export Godot nem o shell Vue completo — só o necessário para **QA + integração**.

---

## Licença

MIT — ver [LICENSE](LICENSE).

---

## Manutenção

- Org: [Copacabana-org](https://github.com/Copacabana-org)
- Issues / PRs neste repositório
- Referência de integração: jogos Template-line (Gelato, CrapsSlot, GTF, …) com `godotMessageReceiver` + dual-iframe
