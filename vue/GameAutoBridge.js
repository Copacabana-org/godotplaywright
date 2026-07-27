/**
 * Godot Playwright — portable Vue shell bridge.
 *
 * Installs `window.__GAME_AUTO__` for Playwright / Python clients.
 * Works with dual-iframe (loader + game) and single-iframe shells.
 *
 * Usage in GamePage.vue (or equivalent):
 *   import { isAutomationEnabled, installGameAutoBridge } from './GameAutoBridge'
 *   // mounted:
 *   if (isAutomationEnabled()) {
 *     this._gameAuto = installGameAutoBridge({
 *       getGodotWindow: () => this.$refs.godotFrame?.contentWindow,
 *     })
 *   }
 *   // inside message handler:
 *   this._gameAuto?.handleParentMessage(event.data)
 */

const PROD_HOSTNAMES = [
  // Deny-list production hosts for EACH game you integrate.
  // Example: 'my-game.casinoapp.live',
]

/** Currencies shared by Template-line Helpers._CURRENCY_DEFAULTS */
export const CURRENCY_PRESETS = {
  BRL: {
    code: 'BRL',
    symbol: 'R$',
    format_precision: '2',
    presentation_multiplier: '1',
    thousand_sep: '.',
    decimal_sep: ',',
  },
  USD: {
    code: 'USD',
    symbol: '$',
    format_precision: '2',
    presentation_multiplier: '1',
    thousand_sep: ',',
    decimal_sep: '.',
  },
  EUR: {
    code: 'EUR',
    symbol: '€',
    format_precision: '2',
    presentation_multiplier: '1',
    thousand_sep: '.',
    decimal_sep: ',',
  },
  GBP: {
    code: 'GBP',
    symbol: '£',
    format_precision: '2',
    presentation_multiplier: '1',
    thousand_sep: ',',
    decimal_sep: '.',
  },
  INR: {
    code: 'INR',
    symbol: '₹',
    format_precision: '2',
    presentation_multiplier: '1',
    thousand_sep: ',',
    decimal_sep: '.',
  },
  RUB: {
    code: 'RUB',
    symbol: '₽',
    format_precision: '2',
    presentation_multiplier: '1',
    thousand_sep: ' ',
    decimal_sep: ',',
  },
  MXN: {
    code: 'MXN',
    symbol: 'MX$',
    format_precision: '2',
    presentation_multiplier: '1',
    thousand_sep: ',',
    decimal_sep: '.',
  },
  ARS: {
    code: 'ARS',
    symbol: '$',
    format_precision: '2',
    presentation_multiplier: '1',
    thousand_sep: '.',
    decimal_sep: ',',
  },
  CLP: {
    code: 'CLP',
    symbol: '$',
    format_precision: '0',
    presentation_multiplier: '1',
    thousand_sep: '.',
    decimal_sep: ',',
  },
  COP: {
    code: 'COP',
    symbol: '$',
    format_precision: '0',
    presentation_multiplier: '1',
    thousand_sep: '.',
    decimal_sep: ',',
  },
  PEN: {
    code: 'PEN',
    symbol: 'S/',
    format_precision: '2',
    presentation_multiplier: '1',
    thousand_sep: ',',
    decimal_sep: '.',
  },
}

export function isAutomationEnabled(options = {}) {
  if (typeof window === 'undefined') return false
  const host = window.location.hostname || ''
  const prodList = options.prodHostnames || PROD_HOSTNAMES
  if (prodList.includes(host)) return false

  const params = new URLSearchParams(window.location.search)
  if (params.has('automation') || params.get('automation') === '1') {
    // explicit opt-in on non-prod
    return true
  }

  if (host === 'localhost' || host === '127.0.0.1') return true
  if (host.startsWith('staging-') || host.startsWith('stag-')) return true
  if (host.startsWith('dev-')) return true
  if (host.startsWith('demo-')) return true
  // Allow force via localStorage for custom QA hosts
  const flag = localStorage.getItem('__GAME_AUTO__')
  return flag === '1' || flag === 'true'
}

/**
 * @param {{ getGodotWindow: () => Window | null | undefined, commandTimeoutMs?: number }} opts
 */
export function installGameAutoBridge(opts) {
  const getGodotWindow = opts.getGodotWindow
  const defaultTimeout = opts.commandTimeoutMs ?? 15000

  // Tell Godot autoload to enable (read at AutomationBridge._ready).
  localStorage.setItem('__GAME_AUTO__', '1')

  let reqSeq = 0
  /** @type {Map<string, { resolve: Function, reject: Function, timer: any }>} */
  const pending = new Map()
  /** @type {Array<{ event: string, data: any, t: number }>} */
  const trackBuffer = []
  const TRACK_BUFFER_MAX = 200
  /** @type {Set<Function>} */
  const trackListeners = new Set()

  let gameLoaded = false
  let loaderDone = false
  let autoReady = false
  /** @type {null | ((v: any) => void)} */
  let resolveReady = null
  const ready = new Promise((resolve) => {
    resolveReady = resolve
  })

  function tryResolveReady() {
    // loaderDone is optional for single-iframe shells (we treat missing loader as done).
    if (gameLoaded && autoReady && resolveReady) {
      resolveReady({ gameLoaded, loaderDone, autoReady })
      resolveReady = null
    }
  }

  function handleParentMessage(data) {
    if (!data || typeof data !== 'object') return

    if (data.status === 'game_loaded') {
      gameLoaded = true
      tryResolveReady()
    }
    if (data.status === 'loader_done') {
      loaderDone = true
      tryResolveReady()
    }
    if (data.status === 'auto_ready') {
      autoReady = true
      tryResolveReady()
    }
    if (data.status === 'auto_result' && data.id != null) {
      const id = String(data.id)
      const entry = pending.get(id)
      if (entry) {
        clearTimeout(entry.timer)
        pending.delete(id)
        if (data.ok) entry.resolve(data.data ?? {})
        else entry.reject(new Error(data.error || 'auto_cmd_failed'))
      }
    }
    if (data.status === 'track' && typeof data.event === 'string') {
      const item = { event: data.event, data: data.data || {}, t: Date.now() }
      trackBuffer.push(item)
      if (trackBuffer.length > TRACK_BUFFER_MAX) trackBuffer.shift()
      for (const cb of trackListeners) {
        try {
          cb(item)
        } catch (_) {
          /* listener errors must not break the bridge */
        }
      }
    }
  }

  function sendToGodot(payload) {
    const win = getGodotWindow?.()
    if (!win || typeof win.godotMessageReceiver !== 'function') {
      throw new Error('godotMessageReceiver not available (game iframe not ready?)')
    }
    win.godotMessageReceiver(JSON.stringify(payload))
  }

  /**
   * @param {string} cmd
   * @param {Record<string, any>} [args]
   * @param {{ timeoutMs?: number }} [options]
   */
  function send(cmd, args = {}, options = {}) {
    const timeoutMs = options.timeoutMs ?? defaultTimeout
    const id = `auto-${++reqSeq}-${Date.now()}`
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        pending.delete(id)
        reject(new Error(`auto cmd timeout: ${cmd} (${timeoutMs}ms)`))
      }, timeoutMs)
      pending.set(id, { resolve, reject, timer })
      try {
        sendToGodot({ action: 'auto', id, cmd, args })
      } catch (err) {
        clearTimeout(timer)
        pending.delete(id)
        reject(err)
      }
    })
  }

  /**
   * Wait for a Godot Tracker event (status:track).
   * Checks buffer first so late subscribers still see recent events.
   */
  function waitTrack(eventName, options = {}) {
    const timeoutMs = options.timeoutMs ?? 30000
    const predicate = options.predicate
    const after = options.after ?? 0

    const match = (item) => {
      if (item.event !== eventName) return false
      if (item.t < after) return false
      if (predicate && !predicate(item.data, item)) return false
      return true
    }

    const existing = [...trackBuffer].reverse().find(match)
    if (existing) return Promise.resolve(existing)

    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        trackListeners.delete(onItem)
        reject(new Error(`waitTrack timeout: ${eventName} (${timeoutMs}ms)`))
      }, timeoutMs)
      function onItem(item) {
        if (!match(item)) return
        clearTimeout(timer)
        trackListeners.delete(onItem)
        resolve(item)
      }
      trackListeners.add(onItem)
    })
  }

  function onTrack(cb) {
    trackListeners.add(cb)
    return () => trackListeners.delete(cb)
  }

  // Single-iframe games never emit loader_done — mark done after a short grace
  // so ready can resolve once game_loaded + auto_ready arrive.
  setTimeout(() => {
    if (!loaderDone) {
      loaderDone = true
      tryResolveReady()
    }
  }, 3000)

  const api = {
    enabled: true,
    protocol: 1,
    ready,
    /** raw command */
    send,
    /** free pointer scripting (viewport coords) */
    move: (x, y) => send('mouse_move', { x, y }),
    mouseDown: (x, y, button = 'left') => send('mouse_down', { x, y, button }),
    mouseUp: (x, y, button = 'left') => send('mouse_up', { x, y, button }),
    click: (x, y, button = 'left') => send('click', { x, y, button }),
    rightClick: (x, y) => send('click', { x, y, button: 'right' }),
    drag: (x1, y1, x2, y2, steps = 10, button = 'left') =>
      send('drag', { x1, y1, x2, y2, steps, button }),
    ping: () => send('ping'),
    getState: () => send('get_state'),
    getHotspots: () => send('get_hotspots'),
    tapControl: (name) => send('tap_control', { name }),
    setLanguage: (code, opts = {}) => send('set_language', { code, ...opts }),
    openMenu: () => send('open_menu'),
    openLanguages: () => send('open_languages'),
    openRules: (opts = {}) => send('open_rules', opts),
    closeRules: () => send('close_rules'),
    openHistory: (opts = {}) => send('open_history', opts),
    closeHistory: () => send('close_history'),
    closeOverlays: () => send('close_overlays'),
    betPlus: (times = 1) => send('bet_plus', { times }),
    betMinus: (times = 1) => send('bet_minus', { times }),
    spin: () => send('spin'),
    /**
     * Runtime currency switch (no remount). Accepts preset code or full format.
     * @param {string | object} currencyOrPreset  e.g. 'USD' or { code, symbol, ... }
     */
    setCurrency: (currencyOrPreset) => {
      let args =
        typeof currencyOrPreset === 'string'
          ? CURRENCY_PRESETS[currencyOrPreset.toUpperCase()]
          : currencyOrPreset
      if (!args) {
        return Promise.reject(new Error(`unknown currency preset: ${currencyOrPreset}`))
      }
      // Normalize preset shape → Godot args
      args = {
        code: args.code || args.currency,
        symbol: args.symbol,
        format_precision: args.format_precision ?? args.precision,
        presentation_multiplier: args.presentation_multiplier ?? '1',
        thousand_sep: args.thousand_sep,
        decimal_sep: args.decimal_sep,
      }
      return send('set_currency', args)
    },
    currencyPresets: CURRENCY_PRESETS,
    reloadConfig: () => send('reload_config'),
    waitTrack,
    onTrack,
    recentTracks: () => trackBuffer.slice(),
    handleParentMessage,
    /** mark signals from host if message event already consumed elsewhere */
    markGameLoaded() {
      gameLoaded = true
      tryResolveReady()
    },
    markLoaderDone() {
      loaderDone = true
      tryResolveReady()
    },
    markAutoReady() {
      autoReady = true
      tryResolveReady()
    },
  }

  window.__GAME_AUTO__ = api
  return api
}

export function uninstallGameAutoBridge() {
  if (window.__GAME_AUTO__) {
    delete window.__GAME_AUTO__
  }
}
