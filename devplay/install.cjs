#!/usr/bin/env node
// Copia o devplay para um repo de jogo.
//
//   node ~/dev/godotplaywright/devplay/install.cjs ~/dev/MeuJogo.Front
//
// Cria <repo>/devplay/ com o runtime, os cenários e um devplay.config.js
// pré-preenchido (título, viewport e nome do export lidos do project.godot).
// Arquivos já existentes não são sobrescritos, exceto com --force.
//
const fs = require('fs')
const path = require('path')

const SRC = __dirname
const target = process.argv[2]
const force = process.argv.includes('--force')

if (!target) {
  console.error('uso: node install.cjs <caminho-do-repo-do-jogo> [--force]')
  process.exit(1)
}

const repo = path.resolve(target)
const dest = path.join(repo, 'devplay')
if (!fs.existsSync(repo)) {
  console.error(`repo não encontrado: ${repo}`)
  process.exit(1)
}

// ── lê o project.godot para pré-preencher a config ──────────────────────────
const projectFile = ['Godot/project.godot', 'project.godot']
  .map((p) => path.join(repo, p))
  .find((p) => fs.existsSync(p))

let name = path.basename(repo).replace(/\.(Front|front)(\.Godot)?$/, '')
let width = 720
let height = 1560
if (projectFile) {
  const src = fs.readFileSync(projectFile, 'utf8')
  name = src.match(/config\/name="([^"]+)"/)?.[1] ?? name
  width = Number(src.match(/window\/size\/viewport_width=(\d+)/)?.[1] ?? width)
  height = Number(src.match(/window\/size\/viewport_height=(\d+)/)?.[1] ?? height)
} else {
  console.warn('aviso: project.godot não encontrado — usando defaults na config')
}

const copy = (rel) => {
  const from = path.join(SRC, rel)
  const to = path.join(dest, rel)
  fs.mkdirSync(path.dirname(to), { recursive: true })
  if (fs.existsSync(to) && !force) return console.log(`  pulado (já existe)  devplay/${rel}`)
  fs.copyFileSync(from, to)
  console.log(`  copiado             devplay/${rel}`)
}

console.log(`instalando devplay em ${dest}`)
copy('devplay.html')
copy('server.cjs')
copy('reference/websocket_bus.gd')
for (const f of fs.readdirSync(path.join(SRC, 'scenarios'))) copy(path.join('scenarios', f))

// ── devplay.config.js ───────────────────────────────────────────────────────
const configPath = path.join(dest, 'devplay.config.js')
if (fs.existsSync(configPath) && !force) {
  console.log('  pulado (já existe)  devplay/devplay.config.js')
} else {
  const config = fs
    .readFileSync(path.join(SRC, 'devplay.config.example.js'), 'utf8')
    .replace(
      /^\/\/ Copie para[\s\S]*?muda de jogo para jogo \(fora o cenário\)\.\n/,
      `// Config do devplay deste jogo. Runtime e cenários: ../devplay/README.md\n`,
    )
    .replace("title: 'EverestRoulette'", `title: '${name}'`)
    .replace("game: '/godot/EverestRoulette.html'", `game: '/godot/${name}.html'`)
    .replace(
      /viewport: \{ width: \d+, height: \d+ \}/,
      `viewport: { width: ${width}, height: ${height} }`,
    )
    .replace("scenario: 'roulette'", "scenario: 'template'")
  fs.writeFileSync(configPath, config)
  console.log('  criado              devplay/devplay.config.js')
}

// ── .gitignore ──────────────────────────────────────────────────────────────
const gitignore = path.join(repo, '.gitignore')
if (fs.existsSync(gitignore)) {
  const src = fs.readFileSync(gitignore, 'utf8')
  if (!src.includes('devplay/godot/')) {
    fs.appendFileSync(gitignore, '\n# export local do devplay\ndevplay/godot/\n')
    console.log('  atualizado          .gitignore (devplay/godot/)')
  }
}

console.log(`
próximos passos:

  1. no script de websocket do jogo, aplique devplay/reference/websocket_bus.gd
     (trata websocket_url == 'broadcast' assinando o BroadcastChannel 'ws_bus')

  2. escreva o cenário: copie devplay/scenarios/template.js e aponte
     devplay/devplay.config.js → scenario: '<nome>'
     eventos do jogo:  grep -rn "event_name ==" Godot/scripts | sort -u

  3. exporte e rode:
     cd Godot && godot --headless --export-release "Web" ../devplay/godot/${name}.html
     node devplay/server.cjs
`)
