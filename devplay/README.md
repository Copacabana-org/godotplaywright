# devplay

Roda o export web do Godot localmente, sem backend: shell Vue e servidor de
rodadas simulados num tab do browser.

**Documentação completa: [../docs/DEVPLAY.md](../docs/DEVPLAY.md).**

```bash
# instalar num jogo
node ~/dev/godotplaywright/devplay/install.cjs ~/dev/MeuJogo.Front

# rodar
cd Godot && godot --headless --export-release "Web" ../devplay/godot/<Jogo>.html
node devplay/server.cjs          # http://localhost:5173/devplay.html
```

| Arquivo | Muda por jogo? |
|---|---|
| `devplay.html` | não — runtime genérico |
| `server.cjs` | não |
| `devplay.config.js` | sim — título, export, viewport, localStorage |
| `scenarios/<jogo>.js` | sim — o protocolo de rodada |
| `api-mocks.json` | opcional — respostas REST específicas |
| `reference/websocket_bus.gd` | trecho a aplicar no `web_socket.gd` do jogo |
| `godot/` | export local, fora do git |
