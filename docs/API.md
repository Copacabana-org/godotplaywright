# API do client

Ambos os clients (JS e Python) expõem a mesma superfície sobre `window.__GAME_AUTO__`.

## Lifecycle

### `waitReady(timeoutMs?)` / `wait_ready(timeout_ms?)`

Espera `window.__GAME_AUTO__.enabled` e a Promise `ready` (game + bridge).

### `send(cmd, args?)`

Comando bruto do protocolo. Prefira os atalhos abaixo.

---

## Pointer

| JS | Python | Notas |
|----|--------|-------|
| `move(x, y)` | `move(x, y)` | Viewport Godot |
| `click(x, y, button?)` | `click(x, y, button?)` | default `left`; ativa `BaseButton` sob o ponto |
| `rightClick(x, y)` | `right_click(x, y)` | |
| `mouseDown(x, y, button?)` | `mouse_down(...)` | |
| `mouseUp(x, y, button?)` | `mouse_up(...)` | |
| `drag(x1,y1,x2,y2, steps?, button?)` | `drag(...)` | |
| `tapControl(name)` | `tap_control(name)` | por nome de nó |
| `getHotspots()` | `get_hotspots()` | lista de alvos visíveis |

Coordenadas = **viewport Godot** (não CSS do browser). Use `getState().viewport`.

---

## Estado

| JS | Python |
|----|--------|
| `ping()` | `ping()` |
| `getState()` | `get_state()` |
| `setCurrency(code\|object)` | `set_currency(...)` |
| `waitTrack(event, { timeoutMs })` | `wait_track(event, timeout_ms)` |

### `getState()` — campos comuns

```json
{
  "protocol": 1,
  "viewport": { "w": 700, "h": 1370 },
  "pointer": { "x": 0, "y": 0 },
  "balance": 10000,
  "current_bet": 1,
  "bet_min": 1,
  "bet_max": 1000,
  "balance_formatted": "R$ 10.000,00",
  "bet_formatted": "R$ 1,00",
  "currency": {
    "code": "BRL",
    "symbol": "R$",
    "format_precision": "2",
    "thousand_sep": ".",
    "decimal_sep": ","
  },
  "language": "pt",
  "game_version": "1.4.0"
}
```

Campos dependem do que o `Helpers` do jogo expõe.

---

## Semântica (Template-line)

| JS | Python | Notas |
|----|--------|-------|
| `setLanguage(code)` | `set_language(code)` | Prefer painel Language |
| `openMenu()` | `open_menu()` | `SideMenu.do_menu` |
| `openLanguages()` | `open_languages()` | item Languages no menu |
| `openRules({ via_menu }?)` | `open_rules(via_menu?)` | Panel Rules (não o Button) |
| `closeRules()` | `close_rules()` | force-hide + limpa dimmer |
| `openHistory({ via_menu }?)` | `open_history(via_menu?)` | Panel History |
| `closeHistory()` | `close_history()` | **não** chama `_hide` (evita reabrir sidebar) |
| `closeOverlays()` | `close_overlays()` | fecha tudo: History, Rules, Language, Support, Autoplay, dimmers, sidebar |
| `betPlus(times?)` | `bet_plus(times?)` | |
| `betMinus(times?)` | `bet_minus(times?)` | |
| `spin()` | `spin()` | |

### `closeOverlays()` — use sempre entre passos de tour

Modais Everest deixam `MenuDimmer` e `SideMenu/Overlay` ativos se só fizerem `hide()` no painel. O cmd força:

- hide de History / Rules / Language / Support / AutoplayPanel / WinOverlay / FreeSpinOverlay  
- `MenuDimmer` hide + mouse ignore  
- `SideMenu/Overlay` alpha 0  
- SideBar fora da tela  

```python
await auto.open_history(via_menu=True)
await auto.close_overlays()   # mesa limpa de novo
await auto.spin()
```

---

## Presets de moeda

Exportados em JS como `CURRENCY_PRESETS` (BRL, USD, EUR, GBP, INR, RUB, MXN, ARS, CLP, COP, PEN).

```js
await auto.setCurrency('USD')
await auto.setCurrency({
  code: 'JPY',
  symbol: '¥',
  format_precision: '0',
  thousand_sep: ',',
  decimal_sep: '.',
  presentation_multiplier: '1',
})
```

> **Nota:** se só a carteira mudar de símbolo e bet/win ficarem com `R$`, o jogo precisa refrescar todos os labels em `update_balance_display` — não é falha do protocolo.

---

## Erros

Comandos rejeitam a Promise se:

- timeout (shell não recebe `auto_result`)
- `ok: false` no result (`error` string no payload)
- `godotMessageReceiver` indisponível (iframe ainda não ready)

Sempre chame `waitReady()` antes dos cmds.
