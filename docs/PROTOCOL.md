# Protocolo godotplaywright

Versão atual do envelope: **1** (`PROTOCOL_VERSION` em `automation_bridge.gd`).

## Shell → Godot

Canal: `iframe.contentWindow.godotMessageReceiver(jsonString)`

```json
{
  "action": "auto",
  "id": "auto-1-1710000000",
  "cmd": "click",
  "args": { "x": 100, "y": 200, "button": "left" }
}
```

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `action` | string | Sempre `"auto"` |
| `id` | string | Correlation id para a Promise no shell |
| `cmd` | string | Comando (tabela abaixo) |
| `args` | object | Argumentos do comando |

### Comandos

#### Core (todo jogo)

| cmd | args | result.data |
|-----|------|-------------|
| `ping` | — | `{ pong, protocol, viewport }` |
| `mouse_move` | `x`, `y` | posição |
| `mouse_down` / `mouse_up` | `x?`, `y?`, `button?` | … |
| `click` | `x`, `y`, `button?`, `activate?` | + `activated` path se botão acionado |
| `drag` | `x1,y1,x2,y2`, `steps?`, `button?` | … |
| `get_state` | — | balance, bet, currency, viewport, … |
| `set_currency` | `code`, `symbol`, `format_precision`, seps… | snapshot currency |
| `reload_config` | — | re-lê Helpers / localStorage |
| `get_hotspots` | — | `{ hotspots: [{ name, path, x, y, w, h }] }` |
| `tap_control` | `name` \| `path` | centro do Control + activate |

Coordenadas: **viewport Godot** (não CSS do browser).

`button`: `"left"` \| `"right"` \| `"middle"`.

#### Template-line (opcional)

| cmd | args | Notas |
|-----|------|--------|
| `set_language` | `code`, `show?` | Prefer Language panel |
| `open_menu` | — | `SideMenu.do_menu` |
| `open_languages` | — | `SideBar._on_languages_pressed` |
| `open_rules` | `via_menu?` | Panel Rules (não o Button homônimo) |
| `close_rules` | — | force-hide + dimmers |
| `open_history` | `via_menu?` | Panel History |
| `close_history` | — | force-hide; **não** chama `_hide` (reabre sidebar) |
| `close_overlays` | — | fecha todos os modais + MenuDimmer + SideMenu/Overlay + SideBar |
| `bet_plus` / `bet_minus` | `times?` | Portrait handlers |
| `spin` | — | Portrait spin |

#### Homônimos perigosos

Vários nós se chamam igual:

| Nome | Button (menu) | Panel (modal) |
|------|---------------|---------------|
| `Rules` | item do SideBar | modal de regras |
| `History` | item do SideBar | modal de histórico |

O bridge resolve pelo **Panel** com `_show` / path `/root/Main/Menu/SideMenu/...`.

## Godot → Shell

Canal: `window.parent.postMessage(payload, '*')` (same-origin recomendado).

### `auto_ready`

```json
{ "status": "auto_ready", "protocol": 1 }
```

Emitido quando o autoload liga com `localStorage.__GAME_AUTO__` truthy.

### `auto_result`

```json
{
  "status": "auto_result",
  "id": "auto-1-…",
  "ok": true,
  "data": { }
}
```

Erro:

```json
{
  "status": "auto_result",
  "id": "…",
  "ok": false,
  "error": "unknown_cmd",
  "data": { }
}
```

### `track` (já existente nos jogos)

```json
{ "status": "track", "event": "spin_result", "data": { "bet": 1, "prize": 0 } }
```

O shell bufferiza esses eventos para `waitTrack(eventName)`.

### Lifecycle (já existente)

| status | Uso no ready |
|--------|----------------|
| `game_loaded` | Jogo montado |
| `loader_done` | Loader sumiu (dual-iframe) |
| `auto_ready` | Bridge aceitando cmds |

`window.__GAME_AUTO__.ready` resolve quando `game_loaded` + `auto_ready` (+ `loader_done` opcional).

## Flag de enable

| Key | Valor | Quem seta |
|-----|-------|-----------|
| `localStorage.__GAME_AUTO__` | `"1"` | Shell ao instalar o bridge |

Godot só processa cmds se a flag estava ligada no `_ready` do autoload (por isso a flag deve existir **antes** do iframe do jogo carregar).

## Segurança

| Host | Comportamento |
|------|----------------|
| Em `PROD_HOSTNAMES` | `isAutomationEnabled()` = false; não instala bridge |
| localhost / staging- / dev- / demo- | enabled |
| Outros + `?automation=1` | enabled se não for prod |

## Compatibilidade

- Bump `PROTOCOL_VERSION` só se quebrar o envelope.
- Novos `cmd` são additive (client antigo ignora).
- Clients novos em jogo antigo: cmds Template-line retornam `ok: false` / `*_not_found` se nós não existirem.
