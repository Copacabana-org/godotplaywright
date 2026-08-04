# CLAUDE.md

Guia para o Claude Code trabalhando neste repo — e, principalmente, para o
Claude Code que for **usar** este repo dentro de um jogo Everest.

## O que é

Duas ferramentas independentes que se compõem:

| Ferramenta | Path | Resolve |
|---|---|---|
| **automation bridge** | `godot/`, `vue/`, `client/` | dirigir o jogo por dentro (clicar em botões nomeados, ler estado, esperar eventos de tracking) — ver [docs/INTEGRATION.md](docs/INTEGRATION.md) |
| **devplay** | `devplay/` | rodar o export web sem backend, com rodadas simuladas — ver [docs/DEVPLAY.md](docs/DEVPLAY.md) |

O bridge precisa de um jogo rodando em algum lugar. O devplay é esse lugar
quando o staging está fora ou quando se quer controlar o resultado da rodada.

---

## Quando usar o devplay (leia isto antes de propor outra coisa)

Use **sempre** que o trabalho for **arte, layout ou posicionamento no export
web**: assets novos, z-index, âncoras, escala, fontes, vídeo de fundo. O editor
do Godot mente sobre o resultado final — `z_as_relative`, ordem de árvore,
canvas stretch e WebP se comportam diferente no export.

Use também para **protocolo de rodada**: forçar um número sorteado, forçar um
crash, engolir uma resposta do servidor para exercitar watchdog.

Não use para lógica pura de GDScript que dá para conferir lendo o código.

## Como o Thiago gosta de usar

Estas preferências vieram da implementação original (Roleta.Front#306) e valem
como default em qualquer jogo:

1. **Playwright sempre em janela visível** (`headless: false`). Ele quer ver a
   janela abrir enquanto você trabalha. Nunca rode headless "para ir mais
   rápido" sem ele pedir.
2. **Iterar por screenshot, não por descrição.** Exporte, tire o print do
   iframe (`game.png`), *olhe* a imagem, compare com o mockup, ajuste, repita.
   Não conclua "deve estar certo agora" sem ter visto.
3. **Compare com a referência de verdade.** Quando houver PNG/PSD de proposta,
   abra e compare lado a lado — ele vai cobrar isso ("compare os resultados com
   a proposta").
4. **Quando a posição depende do gosto dele, pergunte** com opções concretas em
   vez de chutar três vezes. Uma pergunta com preview é mais barata que três
   exports.
5. **Deixe a janela aberta quando ele pedir "abre para eu ver"**: rode em
   background com `KEEP=1` e um `WAIT` longo.
6. **Assets em WebP.** Regra explícita dele para arte nova nos jogos.
7. **Bump de versão é obrigatório** em `Godot/project.godot` →
   `application/config/version`, semver, a cada alteração de frontend. É a
   versão exibida ao jogador e o `game_version` do tracking.
8. **Fechamento de tarefa**: commit em português nas mensagens de UI mas
   **commit/PR/issue em inglês quando o repo já é assim** (siga o repo), push na
   branch de trabalho (normalmente `staging`), comentário de follow-up na issue
   com o que mudou e por quê, e assignee trocado para quem vai validar.

Fluxo típico de um ajuste de arte, ponta a ponta:

```bash
# 1. exportar
cd Godot && godot --headless --export-release "Web" ../devplay/godot/<Jogo>.html

# 2. servidor (uma vez, deixa em background)
node devplay/server.cjs &

# 3. ver
node ~/dev/godotplaywright/examples/devplay_shot.cjs      # janela + game.png
```

Depois: ler `game.png`, ajustar a cena, voltar ao passo 1.

## Timing do screenshot

O `WAIT` decide a fase da rodada que você vai fotografar. Numa roleta,
`WAIT=20000` cai na janela de aposta (vídeo tocando) e `WAIT=45000` cai no giro
(mesa por cima). **Print "errado" muitas vezes é fase errada, não layout
errado** — confira o log do bus que o script imprime antes de mexer na cena.

## Debug de "meu asset não aparece"

Na ordem:

1. O `z_index` está abaixo de algum fundo com `z_as_relative = false`?
   `grep -n "z_index" Godot/scenes/*.tscn`
2. O nó está antes ou depois na árvore? Mesmo z, quem vem depois desenha por cima.
3. O export foi refeito depois da edição da cena?
4. A textura tem alpha? `magick asset.webp -alpha extract -format "%[fx:mean*255]\n" info:`

## Manutenção deste repo

- `devplay/devplay.html` e `devplay/server.cjs` são **genéricos**: se um jogo
  precisar de algo, o caminho é `devplay.config.js` ou um cenário novo, não um
  `if` no runtime. Se não der, generalize aqui e reinstale nos jogos.
- Cenário novo que sirva para uma família de jogos (roleta, crash, slot, bingo)
  vai para `devplay/scenarios/` aqui, não só no repo do jogo.
- Documente em `docs/`, com um resumo curto no README da pasta.
