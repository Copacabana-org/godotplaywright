// Roleta ao vivo (Roleta.Front / ParrotRoulette).
// Ciclo: show-timer → open-bets → close-bets → drawn-number → send-number →
// winner-notification.
export default {
  controls: [
    { id: 'autoLoop', type: 'checkbox', label: 'rodadas automáticas', value: true },
    { id: 'betWindow', type: 'number', label: 'aposta aberta (s)', value: 25 },
    { id: 'forceNumber', type: 'number', label: 'forçar número', value: '', placeholder: 'rnd' },
  ],

  state: { roundId: 1000 },

  async run({ send, sleep, ctl }) {
    const SPIN_DELAY = 3000 // close-bets → drawn-number
    const RESULT_DELAY = 12000 // send-number → próxima rodada
    const betWindow = Math.max(3, Number(ctl('betWindow')) || 25)
    const id = ++this.state.roundId

    send('show-timer', { round_id: id, time: `00:${String(betWindow).padStart(2, '0')}` })
    await sleep(1500)

    send('open-bets', { round_id: id })
    await sleep(betWindow * 1000)

    send('close-bets', { round_id: id })
    await sleep(SPIN_DELAY)

    const forced = ctl('forceNumber')
    const number =
      forced === '' || forced == null
        ? Math.floor(Math.random() * 37)
        : Math.min(36, Math.max(0, Number(forced)))

    send('drawn-number', { round_id: id, number })
    await sleep(1000)

    send('send-number', { round_id: id, number })
    send('winner-notification', { round_id: id, buyer_id: 'devplay', win_total: 0 })
    await sleep(RESULT_DELAY)
  },
}
