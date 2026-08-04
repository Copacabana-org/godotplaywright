// Ponto de partida para um jogo novo. Copie para <jogo>.js e ajuste os eventos.
//
// Descubra os eventos que o jogo escuta com:
//   grep -rn "event_name ==" Godot/scripts | sort -u
//
export default {
  // Controles renderizados no painel lateral. Leia com ctl('<id>').
  controls: [
    { id: 'autoLoop', type: 'checkbox', label: 'rodadas automáticas', value: true },
    { id: 'roundSeconds', type: 'number', label: 'duração (s)', value: 10 },
    // { id: 'boom', type: 'button', label: 'forçar X', onClick: (ctx) => ctx.send('x', {}) },
  ],

  // Se o jogo é quem inicia a rodada (ele manda um join antes), use um id que
  // nunca existe para o runtime não ficar chamando run() em loop.
  // loopControl: 'never',

  // Eventos do jogo que não vale a pena logar.
  mute: ['ping'],

  state: { roundId: 1000 },

  // Um ciclo completo de rodada. O runtime repete enquanto autoLoop estiver ligado.
  async run({ send, sleep, ctl, log }) {
    const id = ++this.state.roundId
    log('sys', `rodada ${id}`)

    send('round-start', { round_id: id })
    await sleep((Number(ctl('roundSeconds')) || 10) * 1000)
    send('round-end', { round_id: id })
    await sleep(3000)
  },

  // Opcional: reage ao que o jogo publica no bus (emit_event do Godot).
  // onGameEvent(ctx, event, message) {},
}
