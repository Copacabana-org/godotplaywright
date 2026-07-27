# Integração em um jogo Godot + Vue

Checklist para plugar **godotplaywright** em qualquer front Everest (ou similar).

## Pré-requisitos

- Godot 4.x, export **Web**
- Shell Vue (ou outro) com o jogo em **iframe same-origin**
- `window.godotMessageReceiver` no iframe do jogo (padrão `broadcast` + `JavaScriptBridge`)

## 1. Godot

### 1.1 Arquivo

```bash
cp godot/automation_bridge.gd  <GameProject>/Scripts/automation_bridge.gd
```

### 1.2 Autoload

Em `project.godot`:

```ini
[autoload]
; ... Helpers, Websocket, Tracker ...
AutomationBridge="*res://Scripts/automation_bridge.gd"
```

Coloque **depois** de `Helpers` se o bridge for usar currency/bet.

### 1.3 Dispatch no receiver JS

Onde você registra `godotMessageReceiver` (quase sempre `main.gd`):

```gdscript
func _on_js_message(js_args: Array) -> void:
	if js_args.is_empty():
		return
	var data = JSON.parse_string(js_args[0])
	if not data is Dictionary:
		return

	if data.has("action"):
		var action := str(data["action"])
		if action == "auto":
			if AutomationBridge:
				AutomationBridge.handle(data)
			return
		_handle_action(action)  # pause_autoplay, etc.
		return

	# ... event/message bus ...
```

### 1.4 Reexport web

Sem reexportar o `.pck`, o autoload não entra no build. Exporte o preset **Web** de novo.

---

## 2. Vue shell

### 2.1 Arquivo

```bash
cp vue/GameAutoBridge.js  <vuejs>/src/services/GameAutoBridge.js
```

### 2.2 Prod hosts (obrigatório)

Edite `PROD_HOSTNAMES` no topo do arquivo (ou passe `prodHostnames` em `isAutomationEnabled({ prodHostnames })`). Hosts nessa lista **nunca** instalam o bridge.

```js
export const PROD_HOSTNAMES = [
  'my-game.casinoapp.live',  // obrigatório por jogo
]
```

**Regras de enable (revisão de segurança):**

| Host | Como liga |
|------|-----------|
| `localhost` / `127.0.0.1` | sempre |
| `staging-*` / `dev-*` / `demo-*` | sempre |
| `*.casinoapp.live` **sem** prefixo de env | **bloqueado** (safety net Everest) |
| Em `PROD_HOSTNAMES` | **bloqueado** |
| Outro host | só `?automation=1` (exato; `?automation=0` **não** liga) |

`localStorage.__GAME_AUTO__` **sozinho** não habilita em host desconhecido/prod — só o shell seta a flag **depois** de `isAutomationEnabled()` passar.

### 2.3 Instalar no GamePage

```js
import { isAutomationEnabled, installGameAutoBridge } from '@/services/GameAutoBridge'

// data()
gameAuto: null,

// mounted()
if (isAutomationEnabled()) {
  this.gameAuto = installGameAutoBridge({
    getGodotWindow: () => this.$refs.godotFrame?.contentWindow,
  })
}

window.addEventListener('message', (event) => {
  this.gameAuto?.handleParentMessage(event.data)
  // ... handlers existentes: game_loaded, track, loader_done ...
})
```

**Dual-iframe:** `getGodotWindow` deve apontar para o iframe do **jogo**, não do loader.

**Single-iframe:** o único iframe Godot. O bridge marca loader “done” sozinho após ~3s se não houver `loader_done`.

### 2.4 Rebuild do shell

```bash
npm run build
```

---

## 3. Client de testes (no repo de QA ou no monorepo)

### Python

```bash
cp -r client/python  my-e2e/godotplaywright/
pip install -r my-e2e/godotplaywright/requirements.txt
playwright install chromium
```

```python
from game_auto import GameAuto
auto = GameAuto(page)
await auto.wait_ready()
```

### JS

```bash
cp client/js/gameAuto.js  e2e/helpers/gameAuto.js
```

```js
import { GameAuto } from './helpers/gameAuto.js'
```

---

## 4. Como o QA sobe o ambiente

| Ambiente | URL típica | Notas |
|----------|------------|--------|
| Staging | `https://staging-…/?automation=1` | Bridge liga por host + query |
| Demo offline | `https://demo-…/` ou `/?demo&automation=1` | Precisa do service worker de demo no **build** |
| Local | `vite preview` + `?demo&automation=1` | `vite dev` costuma **não** servir `demo-sw.js` |

Sinal de pronto para o client:

```js
await page.waitForFunction(() => window.__GAME_AUTO__?.enabled)
await page.evaluate(() => window.__GAME_AUTO__.ready)
```

---

## 5. Estendendo para um jogo específico

Se o jogo não tem `Portrait` / `SideMenu`:

1. Use pointer + `getHotspots` / `tapControl` com os **nomes reais** dos nós.
2. Ou adicione cmds no `automation_bridge.gd` do **seu** fork do jogo (mantenha o protocolo `action:auto`).
3. Ou no client chame handlers via `send('spin')` só se o bridge do jogo implementou o cmd.

Comandos core portáteis (sempre presentes):

`ping`, `mouse_move`, `mouse_down`, `mouse_up`, `click`, `drag`, `get_state`, `set_currency`, `get_hotspots`, `tap_control`

Comandos Template-line (opcionais):

`set_language`, `open_menu`, `open_languages`, `open_rules`, `close_rules`, `open_history`, `close_history`, `close_overlays`, `bet_plus`, `bet_minus`, `spin`

### Armadilha: overlay escuro depois de fechar modal

Fechar só o painel (`History.hide()` / `Rules.hide()`) **não** basta. O shell Everest usa:

- `MenuDimmer` (ColorRect full-screen)
- `SideMenu/Overlay` (véu do drawer)

Sem limpar os dois, a mesa fica escura e cliques parecem “mortos”. Em tours, chame sempre:

```python
await auto.close_overlays()
```

ou os `close_history` / `close_rules` do bridge (já forçam dimmer + sidebar).

---

## 6. Checklist de PR no jogo

- [ ] `automation_bridge.gd` no autoload  
- [ ] `action == "auto"` despachado  
- [ ] `GameAutoBridge.js` + `isAutomationEnabled` + `handleParentMessage`  
- [ ] `PROD_HOSTNAMES` com host de produção **real** do jogo  
- [ ] Smoke: em host de prod (ou `*.casinoapp.live` sem prefixo) `?automation=1` **não** instala bridge  
- [ ] Smoke: `?automation=0` **não** instala bridge  
- [ ] Export web + smoke local: `ping` + `getState`  
- [ ] Smoke: `open_history` → `close_overlays` → mesa **sem** véu escuro  
- [ ] Confirmar que em prod `window.__GAME_AUTO__` **não** existe  

### Relação monorepo vs pacote

- **Fonte canônica:** [Copacabana-org/godotplaywright](https://github.com/Copacabana-org/godotplaywright)
- Em monorepo de **jogo**, **não** commite uma segunda cópia byte-a-byte em `everest-game-auto/` + `Scripts/` + sync script. Prefira:
  - submodule / sparse checkout do pacote, ou
  - symlink `Godot/Scripts/automation_bridge.gd` → path do pacote, ou
  - uma única cópia no jogo (sem pasta espelho)
- `examples/` vivem no **pacote** (docs de QA); não precisam ir no PR do jogo nem no CI do jogo até haver job real.

