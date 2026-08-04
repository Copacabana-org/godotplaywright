# Trecho de referência para o script de WebSocket do jogo (o autoload que
# embrulha o SocketIOClient — geralmente scripts/web_socket.gd).
#
# Ideia: quando `websocket_url == 'broadcast'`, em vez de abrir um socket real o
# jogo assina o BroadcastChannel 'ws_bus' e trata cada `{event, message}` que
# chega como se viesse do servidor. `emit_event()` publica de volta no mesmo bus.
#
# Não é um arquivo para copiar inteiro: cole os três blocos abaixo no script que
# já existe no jogo, mantendo o nome do handler de evento local.

# ── 1. campos ────────────────────────────────────────────────────────────────

var _bus: JavaScriptObject = null
var _bus_callback: JavaScriptObject = null


# ── 2. no _ready(), antes de instanciar o SocketIOClient ─────────────────────

#	var websocket_url = Helpers.get_websocket_url()
#
#	if websocket_url == 'broadcast':
#		_setup_broadcast_bus()
#		return


# ── 3. os métodos do bus ─────────────────────────────────────────────────────

func _setup_broadcast_bus() -> void:
	if not OS.has_feature("web"):
		return
	_bus = JavaScriptBridge.create_object("BroadcastChannel", "ws_bus")
	if _bus == null:
		push_error("Failed to create BroadcastChannel('ws_bus')")
		return
	_bus_callback = JavaScriptBridge.create_callback(Callable(self, "_on_bus_message"))
	_bus.onmessage = _bus_callback
	connection_established.emit()


func _on_bus_message(args: Array) -> void:
	if args.is_empty():
		return
	var parsed = JSON.parse_string(str(args[0].data))
	if not parsed is Dictionary:
		return
	if parsed.has("event") and parsed.has("message"):
		# _on_socket_event é o handler que o jogo já usa para eventos do socket.
		_on_socket_event(str(parsed["event"]), parsed["message"], null)


# E em emit_event(), publique no bus quando ele existir:
#
#	func emit_event(event_name: String, data: Variant = null):
#		if _bus != null:
#			_bus.postMessage(JSON.stringify({"event": event_name, "message": data}))
#			return
#		client.socketio_send(event_name, data)
