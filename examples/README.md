# Examples

Scripts de referência. Ajuste `BASE_URL` para o jogo sob teste.

```bash
export BASE_URL=http://127.0.0.1:4174          # vite preview + ?demo
# export BASE_URL=https://staging-my-game.example

cd client/python && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && playwright install chromium
cd ../../examples
```

| Script | Headed? | Descrição |
|--------|---------|-----------|
| `smoke_pointer.py` | não | ping + pointer básico |
| `currency_matrix.py` | não | loop de moedas preset |
| `practical_test.py` | não | suíte de asserts (pointer + currency) |
| `demo_visible.py` | **sim** | pointer livre lento (gravação) |
| `demo_play_flow.py` | **sim** | pt → bet+ → spin |
| `demo_menu_lang_spin.py` | **sim** | pt → menu → muda idioma → bet → spin |
| `demo_rules_i18n_shots.py` | **sim** | regras nas N línguas + PNG em `OUT_DIR` |
| `demo_full_screen_tour.py` | **sim** | tour completo: telas + animações + PNGs |
| `playwright.spec.mjs` | — | esqueleto `@playwright/test` |

---

## Tour completo (recomendado para regressão visual)

Percorre idioma, menu, history, rules, currency, autoplay, bet, spin (burst de frames) e grava tudo.

```bash
OUT_DIR=/tmp/godot_tour \
STEP_PAUSE=0.8 \
SPIN_BURST_N=12 \
BURST_MS=260 \
BASE_URL=http://127.0.0.1:4174 \
python demo_full_screen_tour.py
```

Saída:

```
/tmp/godot_tour/
  001_00_navigate_shell.png
  022_12_main_after_history_game.png   # deve estar limpo (sem History / dimmer)
  058_27_spin_anim_06_game.png         # reels visíveis
  073_30_final_game.png
  index.md
  manifest.json
```

O script chama `close_overlays()` entre passos para evitar o véu escuro.

---

## Screenshots de regras (i18n)

```bash
OUT_DIR=/tmp/rules_i18n \
LANGS=pt,en,es,hi,ru \
STEP_PAUSE=2.5 \
BASE_URL=http://127.0.0.1:4174 \
python demo_rules_i18n_shots.py
```

---

## Notas

- Demo offline (`?demo`) exige **build + preview** do shell; `vite dev` geralmente não registra o service worker.
- Ações semânticas (`spin`, `open_rules`, …) exigem nós Template-line; senão use `get_hotspots` + `click`.
- `close_rules` / `close_history` fecham o **Panel** modal, não o Button do menu com o mesmo nome.
- Depois de qualquer modal: `close_overlays()` se a mesa continuar escura.
