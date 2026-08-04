// Crash / Aviator (GTF.Front).
// O jogo dirige a rodada: manda crash:join_room e crash:cashout, o cenário
// responde com joined/start/tick/cashout_ok/crashed/result.
const GROWTH = 0.000126
const rollCrash = () => Math.min(100, Math.max(1.01, 0.97 / Math.max(1 - Math.random(), 1e-4)))

let R = null
let tickTimer = null

export default {
  loopControl: 'never', // quem inicia a rodada é o jogo, não o loop do runtime

  controls: [
    { id: 'autoCrash', type: 'checkbox', label: 'crash automático', value: true },
    { id: 'silentFull', type: 'checkbox', label: 'ignorar cashout FULL (watchdog)', value: false },
    {
      id: 'forceCrash',
      type: 'button',
      label: 'forçar CRASH agora',
      onClick: (ctx) => crash(ctx),
    },
  ],

  async run({ sleep }) {
    await sleep(1000) // ocioso: a rodada nasce do crash:join_room do jogo
  },

  onGameEvent(ctx, event, message) {
    if (event === 'crash:join_room') joinRoom(ctx, message.round_uuid)
    else if (event === 'crash:cashout') cashout(ctx, message.type)
  },
}

const mult = () => Math.exp(GROWTH * (Date.now() - R.t0))

function joinRoom(ctx, round_uuid) {
  R = { uuid: round_uuid, t0: Date.now(), stake: 1, half_used: false, crash_at: rollCrash(), over: false }
  ctx.log('sys', `rodada ${round_uuid} — crash sorteado em ${R.crash_at.toFixed(2)}x`)

  ctx.send('crash:joined', { round_uuid, t0: R.t0, growth_rate: GROWTH, server_time: Date.now() })
  ctx.send('crash:start', { round_uuid, t0: R.t0, growth_rate: GROWTH })

  clearInterval(tickTimer)
  tickTimer = setInterval(() => {
    if (!R || R.over) return
    const m = mult()
    if (ctx.ctl('autoCrash') && m >= R.crash_at) return crash(ctx)
    ctx.sendQuiet('crash:tick', { round_uuid: R.uuid, multiplier: m })
  }, 100)
}

function crash(ctx) {
  if (!R || R.over) return
  R.over = true
  clearInterval(tickTimer)
  const at = Math.min(mult(), R.crash_at)
  ctx.send('crash:crashed', { round_uuid: R.uuid, crash_at: at })
  ctx.send('crash:result', {
    round_uuid: R.uuid,
    outcome: R.half_used ? 'partial_win' : 'loss',
    payout: 0,
    crash_at: at,
  })
}

function cashout(ctx, type) {
  if (!R || R.over) return
  const m = mult()
  if (type === 'half') {
    if (R.half_used) return ctx.send('crash:error', { round_uuid: R.uuid, code: 'half_already_used' })
    const payout = R.stake * 0.5 * m
    R.half_used = true
    R.stake *= 0.5
    return ctx.send('crash:cashout_ok', { round_uuid: R.uuid, type: 'half', mult: m, payout })
  }
  if (ctx.ctl('silentFull')) {
    ctx.log('sys', 'cashout FULL engolido de propósito (teste do watchdog)')
    return
  }
  R.over = true
  clearInterval(tickTimer)
  const payout = R.stake * m
  ctx.send('crash:cashout_ok', { round_uuid: R.uuid, type: 'full', mult: m, payout })
  ctx.send('crash:result', { round_uuid: R.uuid, outcome: 'win', payout })
}
