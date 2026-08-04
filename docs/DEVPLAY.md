# devplay — rodar o export web sem backend

Harness local para abrir o **export web do Godot** num browser real, com o shell
Vue simulado e o servidor de rodadas simulado, **sem depender do staging**.

Serve para o que o `automation_bridge.gd` não cobre: conferir **layout e arte no
export web de verdade** (o editor mente sobre z-index, escala de canvas, WebP,
vídeo), iterar num ajuste de posição em ciclos de segundos, e exercitar o
protocolo de rodada isoladamente — inclusive casos que o servidor real não
produz sob demanda (número forçado, crash forçado, resposta engolida).

Nasceu no GTF.Front, foi generalizado ao ser portado para Roleta.Front
(issue Copacabana-org/Roleta.Front#306).

---

## Como funciona

```
devplay.html  (tab do browser)
   │  localStorage: api_url, websocket_url='broadcast', session, balance…
   │  BroadcastChannel('ws_bus')  ← servidor de rodadas simulado
   ▼
iframe  godot/<Jogo>.html   (export web, mesmo origin)
   │  web_socket.gd vê websocket_url == 'broadcast'
   │  assina o ws_bus em vez de abrir o SocketIOClient
   ▼
o jogo recebe show-timer / open-bets / … como se viesse do servidor
```

Três peças:

| Peça | Papel |
|---|---|
| `devplay/devplay.html` | runtime genérico: semeia localStorage, embute o iframe, roda o cenário, mostra o log bidirecional. **Não muda de jogo para jogo.** |
| `devplay/devplay.config.js` | o que muda: título, caminho do export, viewport, localStorage, qual cenário usar |
| `devplay/scenarios/<jogo>.js` | o protocolo de rodada daquele jogo |

Mais o `devplay/server.cjs`: servidor estático burro em `:5173` que serve
`devplay/` e devolve JSON em `/api/*`, para o jogo não travar em request pendente.

### Por que BroadcastChannel e não um socket

O `ws_bus` é escopado por **origin**, então a página e o iframe do jogo têm que
ser servidos pelo mesmo host — daí o `server.cjs` servir os dois. Em troca não
precisa de servidor Socket.IO, de handshake, nem de rede: o "servidor" é
JavaScript no mesmo tab, que o Playwright pode inspecionar e dirigir.

### Por que fora de `public/`

Em jogos que têm o shell Vue no mesmo repo, `devplay/` **não** vai em `public/`:
entraria no `dist/` de produção. Fica na raiz do repo e é servido só pelo
`server.cjs` (ou por um middleware dev-only no `vite.config.js`, como no GTF).

---

## Instalar num jogo novo

```bash
node ~/dev/godotplaywright/devplay/install.cjs ~/dev/MeuJogo.Front
```

Copia o runtime, os cenários e gera um `devplay.config.js` com título, viewport e
nome do export lidos do `project.godot`. Também acrescenta `devplay/godot/` ao
`.gitignore` (o export é local, não vai para o git). Não sobrescreve nada sem `--force`.

Depois, três passos:

**1. Lado Godot.** No autoload de websocket do jogo (normalmente
`Godot/scripts/web_socket.gd`), aplique os blocos de
[`devplay/reference/websocket_bus.gd`](../devplay/reference/websocket_bus.gd):
quando `websocket_url == 'broadcast'`, assine o `ws_bus` em vez de instanciar o
`SocketIOClient`, e publique de volta no bus em `emit_event()`.

Vários jogos Everest **já** têm o `if websocket_url == 'broadcast': return` —
só falta trocar o `return` pelo `_setup_broadcast_bus()`.

**2. Cenário.** Descubra os eventos que o jogo escuta:

```bash
grep -rn "event_name ==" Godot/scripts | sort -u
```

Copie `devplay/scenarios/template.js` e emita esses eventos na ordem certa.
Aponte `devplay.config.js` → `scenario: '<nome>'`.

**3. Exporte e rode.**

```bash
cd Godot && godot --headless --export-release "Web" ../devplay/godot/<Jogo>.html
node devplay/server.cjs
```

Abra <http://localhost:5173/devplay.html>.

---

## Escrever um cenário

```js
export default {
  controls: [
    { id: 'autoLoop', type: 'checkbox', label: 'rodadas automáticas', value: true },
    { id: 'roundSeconds', type: 'number', label: 'duração (s)', value: 10 },
    { id: 'boom', type: 'button', label: 'forçar X', onClick: (ctx) => ctx.send('x', {}) },
  ],

  state: { roundId: 1000 },

  async run({ send, sleep, ctl, log }) {
    const id = ++this.state.roundId
    send('round-start', { round_id: id })
    await sleep((Number(ctl('roundSeconds')) || 10) * 1000)
    send('round-end', { round_id: id })
  },

  onGameEvent(ctx, event, message) {},  // opcional
}
```

O runtime chama `run()` em loop enquanto o checkbox `autoLoop` estiver ligado.

| Campo do `ctx` | Para quê |
|---|---|
| `send(event, message)` | publica no bus **e** loga |
| `sendQuiet(event, message)` | publica sem logar — para ticks de alta frequência |
| `sleep(ms)` | espera |
| `ctl(id)` | valor atual de um controle |
| `log(cls, msg)` | escreve no painel (`'sys'`, `'in'`, `'out'`, `'err'`) |

Quando **o jogo** é quem inicia a rodada (manda um `join` e espera resposta,
como o crash), ponha `loopControl: 'never'` e faça o trabalho em `onGameEvent`.
Veja [`scenarios/crash.js`](../devplay/scenarios/crash.js) para esse formato e
[`scenarios/roulette.js`](../devplay/scenarios/roulette.js) para o formato
"servidor dirige a rodada".

### Mocks de REST

Endpoints que o Godot chama direto (`ApiRequester`) caem em
`{ success: true, errors: null, data: {} }`. Para respostas específicas, crie
`devplay/api-mocks.json`:

```json
{ "last-five-rounds": { "success": true, "data": [] } }
```

A chave casa por prefixo do caminho depois de `/api/`. O arquivo é relido a cada
request — dá para editar sem reiniciar o servidor.

---

## Usar com Playwright

```bash
node devplay/server.cjs &
node ~/dev/godotplaywright/examples/devplay_shot.cjs
```

[`examples/devplay_shot.cjs`](../examples/devplay_shot.cjs) abre **em janela
visível**, espera `WAIT` ms, e salva dois PNG:

- `game.png` — só o iframe do jogo. É este que se compara com o mockup.
- `devplay.png` — a janela inteira, com o painel de log.

```bash
WAIT=45000 node examples/devplay_shot.cjs      # pega uma fase mais tarde da rodada
KEEP=1 WAIT=900000 node examples/devplay_shot.cjs &   # deixa a janela aberta
```

O timing importa: numa roleta, `WAIT=20000` cai na janela de aposta (vídeo
tocando) e `WAIT=45000` cai no giro. Se o screenshot saiu "errado", confira a
fase antes de mexer no layout.

Para automação semântica de verdade (clicar em botões nomeados, ler estado do
jogo), o devplay compõe com o `automation_bridge.gd` — veja
[INTEGRATION.md](INTEGRATION.md). O devplay entrega o jogo rodando; o bridge
entrega o controle dentro do canvas.

---

## Armadilhas conhecidas

**z-index negativo no Godot.** Muitos jogos Everest têm um sprite de fundo com
`z_index = -1` e `z_as_relative = false`. Qualquer coisa abaixo disso some atrás
do fundo. Se um asset novo "não renderiza", cheque:

```bash
grep -n "z_index" Godot/scenes/scn_main.tscn
```

**Ordem na árvore desempata o mesmo z.** Dois nós com o mesmo `z_index`: quem
vem depois na cena desenha por cima. Foi assim que as cortinas da roleta
ficaram acima do vídeo e abaixo da mesa, todos em `z_index = -1`.

**O export tem que ser reescrito a cada mudança.** O `server.cjs` manda
`Cache-Control: no-store`, mas o `godot --headless --export-release` precisa
rodar de novo — o browser não lê a cena do editor.

**Vídeo/áudio remoto.** Se o jogo baixa mídia de CDN, o devplay continua
baixando de verdade. Sem rede, a área fica preta — não é bug de layout.

**`thread_support`.** Com `variant/thread_support=true` no `export_presets.cfg`,
o export precisa dos headers COOP/COEP e o `server.cjs` não os manda. Ou
desligue o thread support no preset de dev, ou acrescente os headers.
