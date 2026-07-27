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
| `playwright.spec.mjs` | — | esqueleto `@playwright/test` |

## Screenshots de regras

```bash
OUT_DIR=/tmp/rules_i18n \
LANGS=pt,en,es,hi,ru \
STEP_PAUSE=2.5 \
BASE_URL=http://127.0.0.1:4174 \
python demo_rules_i18n_shots.py
```

Saída: `/tmp/rules_i18n/rules_01_pt.png`, `…_iframe.png`, `index.md`.

## Notas

- Demo offline (`?demo`) exige **build + preview** do shell; `vite dev` geralmente não registra o service worker.
- Ações semânticas (`spin`, `open_rules`, …) exigem nós Template-line no jogo; senão use `get_hotspots` + `click`.
- `close_rules` fecha o **Panel** `Rules`, não o Button homônimo do menu (isso já está no bridge).
