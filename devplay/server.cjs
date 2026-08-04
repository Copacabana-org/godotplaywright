// Servidor estático dev-only do devplay.
//
// Serve a pasta devplay/ (incluindo o export web em devplay/godot/) e responde
// os endpoints REST que o Godot chama direto, para o jogo não travar em request
// pendente. É de propósito burro: sem build, sem dependência, sem watch.
//
//   node devplay/server.cjs
//   PORT=5174 node devplay/server.cjs
//
// Mocks de API: crie devplay/api-mocks.json com { "<prefixo>": <resposta> }, ex.
//   { "last-five-rounds": { "success": true, "data": [] } }
// Qualquer /api/* sem match cai no fallback DEFAULT_API_RESPONSE.
//
const http = require('http')
const fs = require('fs')
const path = require('path')

const ROOT = __dirname
const PORT = Number(process.env.PORT || 5173)
const DEFAULT_API_RESPONSE = { success: true, errors: null, data: {} }

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript',
  '.mjs': 'text/javascript',
  '.css': 'text/css',
  '.wasm': 'application/wasm',
  '.pck': 'application/octet-stream',
  '.png': 'image/png',
  '.webp': 'image/webp',
  '.jpg': 'image/jpeg',
  '.svg': 'image/svg+xml',
  '.json': 'application/json',
  '.ogv': 'video/ogg',
  '.ogg': 'audio/ogg',
  '.mp3': 'audio/mpeg',
  '.wav': 'audio/wav',
  '.zip': 'application/zip',
  '.ttf': 'font/ttf',
  '.woff2': 'font/woff2',
}

const CORS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': '*',
  'Access-Control-Allow-Methods': 'GET,POST,PUT,PATCH,DELETE,OPTIONS',
}

const mocksPath = path.join(ROOT, 'api-mocks.json')
const loadMocks = () => {
  try {
    return JSON.parse(fs.readFileSync(mocksPath, 'utf8'))
  } catch {
    return {}
  }
}

const json = (res, body) => {
  res.writeHead(200, { 'Content-Type': 'application/json', ...CORS })
  res.end(JSON.stringify(body))
}

const server = http.createServer((req, res) => {
  const url = new URL(req.url, `http://localhost:${PORT}`)

  if (req.method === 'OPTIONS') {
    res.writeHead(204, CORS)
    return res.end()
  }

  // API mockada -------------------------------------------------------------
  if (url.pathname.startsWith('/api/')) {
    const rest = url.pathname.slice('/api/'.length)
    const mocks = loadMocks() // relido a cada request: edite o JSON sem reiniciar
    const hit = Object.keys(mocks).find((k) => rest.startsWith(k))
    if (process.env.DEVPLAY_VERBOSE) console.log(`[api] ${req.method} ${url.pathname}`)
    return json(res, hit ? mocks[hit] : DEFAULT_API_RESPONSE)
  }

  // Estático ----------------------------------------------------------------
  let rel = decodeURIComponent(url.pathname)
  if (rel === '/') rel = '/devplay.html'
  const file = path.join(ROOT, path.normalize(rel).replace(/^(\.\.[/\\])+/, ''))
  if (!file.startsWith(ROOT) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) {
    res.writeHead(404, CORS)
    return res.end('not found')
  }
  res.writeHead(200, {
    'Content-Type': MIME[path.extname(file)] || 'application/octet-stream',
    'Cache-Control': 'no-store', // o export é reescrito o tempo todo durante o ajuste
    ...CORS,
  })
  fs.createReadStream(file).pipe(res)
})

server.listen(PORT, () => {
  console.log(`devplay em http://localhost:${PORT}/devplay.html`)
  if (!fs.existsSync(path.join(ROOT, 'godot'))) {
    console.warn('aviso: devplay/godot/ não existe — exporte o jogo antes de abrir')
  }
})
