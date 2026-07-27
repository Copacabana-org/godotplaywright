# Segurança

O bridge injeta input e pode disparar spin/bet/currency. **Nunca** deve rodar em produção com dinheiro real.

## Modelo de enable

Implementado em `isAutomationEnabled()` / `isProductionHost()` (`vue/GameAutoBridge.js`).

```
isProductionHost(host)?  →  false (nunca)
isTrustedNonProd(host)?  →  true  (localhost, staging-*, dev-*, demo-*)
?automation=1|true?      →  true  (só se não for production)
else                     →  false
```

### Correções vs bugs reportados (review CrapsSlot #18)

| Problema | Fix |
|----------|-----|
| `params.has('automation')` ligava com qualquer valor (`?automation=0`) | só `=== '1'` ou `=== 'true'` |
| `PROD_HOSTNAMES` vazio + `?automation=1` em prod real | deny-list + **safety net** `*.casinoapp.live` sem prefixo de env |
| `localStorage.__GAME_AUTO__` sozinho em host desconhecido | flag só é setada **depois** de `isAutomationEnabled()`; localStorage sozinho não habilita |

### Checklist de integração

1. Preencher `PROD_HOSTNAMES` com o host de prod do jogo.
2. Nunca instalar o bridge fora de `if (isAutomationEnabled())`.
3. Não setar `localStorage.__GAME_AUTO__ = '1'` no shell sem passar pelo gate.
4. Smoke: abrir `https://<prod>/?automation=1` → `window.__GAME_AUTO__` deve ser `undefined`.

### Godot

O autoload só lê `localStorage.__GAME_AUTO__` no `_ready`. Se o shell não setar a flag (gate falhou), o bridge Godot fica inerte mesmo que o `.pck` a contenha.
