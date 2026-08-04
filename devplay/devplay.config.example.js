// Copie para devplay/devplay.config.js e ajuste. Este é o ÚNICO arquivo que
// muda de jogo para jogo (fora o cenário).
export default {
  title: 'EverestRoulette',

  // Caminho do export web, relativo à raiz servida (devplay/).
  game: '/godot/EverestRoulette.html',

  // Resolução do projeto Godot (project.godot → display/window/size).
  viewport: { width: 720, height: 1560 },

  // Arquivo em devplay/scenarios/ que dirige a rodada.
  scenario: 'roulette',

  // Quanto do espaço horizontal o iframe pode ocupar (o resto é o painel).
  stageRatio: 0.55,

  // Espera antes do primeiro ciclo, para o WASM carregar.
  startDelayMs: 6000,

  // localStorage que o shell Vue normalmente injeta. websocket_url, api_url,
  // cms_url, session e user_id já vêm com default — sobrescreva se precisar.
  storage: {
    balance: '1000',
    bet_min: '1',
    bet_max: '500',
    currency_symbol: 'R$',
    currency_format_precision: '2',
    currency_presentation_multiplier: '1',
    coins_values: '[1,5,25,100]',
    locale: 'pt',
    language: 'pt',
    // use null para limpar uma chave que atrapalhe entre execuções:
    // some_pending_round: null,
  },
}
